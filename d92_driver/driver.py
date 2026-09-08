"""Low-level but friendly driver for the MiraBox D92.

The D92 appears as a standard HID device.  It accepts 1024-byte payloads;
hidapi requires one additional byte at the beginning for the report ID.
The display protocol discovered for this device uses report ID 0 and the
following commands:

    DIS       wake the display
    CLE       clear the display
    LIG       set brightness (0..100)
    CONNECT   keep the display alive
    DRA ...   transfer a JPEG frame
    STP       commit the transferred frame

This module deliberately keeps the protocol details here, so applications
only need to call methods such as ``send_image`` and ``keep_alive``.
"""

from __future__ import annotations

import struct
import threading
from io import BytesIO
from pathlib import Path
from typing import Optional

import hid
from PIL import Image


class D92Error(RuntimeError):
    """Raised when the D92 cannot be found or rejects a HID write."""


class D92Driver:
    """Connection and protocol wrapper for one MiraBox D92 monitor."""

    VID = 0x5548
    PID = 0x1011
    PAYLOAD_SIZE = 1024
    REPORT_SIZE = PAYLOAD_SIZE + 1

    def __init__(self, device: hid.device):
        self._device = device
        self._lock = threading.Lock()

    @classmethod
    def open(cls, path: Optional[str | bytes] = None) -> "D92Driver":
        """Open the first D92, or the HID device specified by ``path``."""
        devices = hid.enumerate(cls.VID, cls.PID)
        if not devices:
            raise D92Error("MiraBox D92 not found")

        selected_path = path if path is not None else devices[0]["path"]
        device = hid.device()
        device.open_path(selected_path)
        return cls(device)

    def close(self) -> None:
        """Close the HID handle."""
        self._device.close()

    def __enter__(self) -> "D92Driver":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _write_payload(self, payload: bytes) -> None:
        """Write exactly one zero-padded HID output report."""
        if len(payload) > self.PAYLOAD_SIZE:
            raise D92Error("HID payload is larger than 1024 bytes")

        packet = b"\x00" + payload.ljust(self.PAYLOAD_SIZE, b"\x00")
        written = self._device.write(packet)
        if written != self.REPORT_SIZE:
            raise D92Error(f"short HID write: {written} bytes")

    def command(self, command: bytes, params: bytes = b"", gap: int = 2) -> None:
        """Send a regular ``CRT 00 00 <command>`` protocol command."""
        payload = b"CRT\x00\x00" + command + b"\x00" * gap + params
        with self._lock:
            self._write_payload(payload)

    def wake(self) -> None:
        """Wake the display (protocol command ``DIS``)."""
        self.command(b"DIS")

    def connect(self) -> None:
        """Send one keep-alive heartbeat (protocol command ``CONNECT``)."""
        self.command(b"CONNECT")

    def set_brightness(self, percent: int) -> None:
        """Set brightness to an integer percentage from 0 through 100."""
        if not 0 <= percent <= 100:
            raise ValueError("brightness must be between 0 and 100")
        # CRT 00 00 LIG 00 00 <brightness>
        self.command(b"LIG", bytes([percent]), gap=2)

    def clear(self) -> None:
        """Clear the screen using the D92-specific ``CLE`` layout."""
        with self._lock:
            self._write_payload(b"CRT\x00\x00CLE\x00\x00\x00\xFF")

    def send_jpeg(self, jpeg: bytes) -> None:
        """Send one already encoded fullscreen JPEG and commit it."""
        header = bytearray(32)
        header[0:3] = b"CRT"
        header[5:8] = b"DRA"
        header[8:12] = struct.pack(">I", len(header) + len(jpeg))
        data = bytes(header) + jpeg

        with self._lock:
            for offset in range(0, len(data), self.PAYLOAD_SIZE):
                self._write_payload(data[offset:offset + self.PAYLOAD_SIZE])
            # STP commits the complete frame.  Write it directly here because
            # the lock is already held for the whole multi-report transfer.
            self._write_payload(b"CRT\x00\x00STP\x00\x00")

    def send_image(self, filename: str | Path, quality: int = 95) -> None:
        """Rotate, encode and send a fullscreen image.

        The physical panel is 1920x462, while the wire JPEG is portrait
        462x1920.  The clockwise rotation is done here, once per call.
        """
        image = Image.open(filename).convert("RGB")
        if image.size != (1920, 462):
            image = image.resize((1920, 462))
        image = image.transpose(Image.Transpose.ROTATE_270)

        output = BytesIO()
        image.save(output, format="JPEG", quality=quality, subsampling=0)
        self.send_jpeg(output.getvalue())
