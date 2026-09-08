"""Send one image to the MiraBox D92."""

from pathlib import Path
import time

from d92_driver import D92Driver


IMAGE = Path(__file__).with_name("test.jpg")


def main() -> None:
    with D92Driver.open() as display:
        display.wake()
        display.clear()
        display.send_image(IMAGE)
        print(f"Displayed: {IMAGE.name}")
        print("Sending CONNECT every 4 seconds. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(4)
                display.connect()
        except KeyboardInterrupt:
            print("\nDone.")


if __name__ == "__main__":
    main()
