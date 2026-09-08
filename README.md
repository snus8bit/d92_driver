# MiraBox D92 HID Driver

A small Python driver for the MiraBox D92 USB/HID monitor.

Tested with a device using VID `0x5548` and PID `0x1011`. The driver sends
full-screen JPEG frames through the standard Windows HID driver.

## Installation

```powershell
python -m pip install hidapi pillow
```

## Usage

Place an image named `test.jpg` next to the scripts and run:

```powershell
python send_image.py
```

To measure the maximum full-frame transfer rate:

```powershell
python fps_test.py
```

The tested device reached approximately 28 stable FPS.

## Package

The `d92_driver` module provides the `D92Driver` class with `wake`, `clear`,
`set_brightness`, `connect`, `send_image`, and `send_jpeg` methods.

`send_image` resizes the image to 1920x462, rotates it by 90 degrees, and
encodes it as JPEG. During idle periods, call `connect` periodically to keep
the display alive. Continuous frame transmission makes a separate heartbeat
unnecessary.

The protocol was investigated on one MiraBox D92 unit. Compatibility with
other hardware revisions is not guaranteed.
