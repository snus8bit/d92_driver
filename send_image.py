"""Send one image to the MiraBox D92."""

from pathlib import Path

from d92_driver import D92Driver


IMAGE = Path(__file__).with_name("test.jpg")


def main() -> None:
    with D92Driver.open() as display:
        display.wake()
        display.clear()
        display.send_image(IMAGE)
        print(f"Displayed: {IMAGE.name}")
        print("Press Ctrl+C to stop.")
        try:
            while True:
                input("Press ENTER to send CONNECT (or Ctrl+C to exit)...")
                display.connect()
        except KeyboardInterrupt:
            print("\nDone.")


if __name__ == "__main__":
    main()
