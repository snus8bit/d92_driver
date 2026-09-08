"""Measure the maximum fullscreen JPEG frame rate of the MiraBox D92."""

from pathlib import Path
from time import perf_counter
from io import BytesIO

from PIL import Image
from d92_driver import D92Driver


IMAGE = Path(__file__).with_name("test.jpg")


def main() -> None:
    # Encode once: this test measures full-frame USB/HID throughput.
    image = Image.open(IMAGE).convert("RGB")
    if image.size != (1920, 462):
        image = image.resize((1920, 462))
    image = image.transpose(Image.Transpose.ROTATE_270)
    output = BytesIO()
    image.save(output, format="JPEG", quality=95, subsampling=0)
    jpeg = output.getvalue()

    with D92Driver.open() as display:
        display.wake()
        display.clear()
        print(f"JPEG: {len(jpeg)} bytes")
        print("Sending full frames. Press Ctrl+C to stop.")
        frames = 0
        started = perf_counter()
        last_time = started
        last_frames = 0
        try:
            while True:
                display.send_jpeg(jpeg)
                frames += 1
                now = perf_counter()
                if now - last_time >= 1:
                    print(
                        f"FPS: {frames / (now - started):.2f} "
                        f"(interval: {(frames - last_frames) / (now - last_time):.2f})"
                    )
                    last_time = now
                    last_frames = frames
        except KeyboardInterrupt:
            elapsed = perf_counter() - started
            print(f"\nAverage FPS: {frames / elapsed:.2f}")


if __name__ == "__main__":
    main()
