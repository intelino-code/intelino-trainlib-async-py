"""Example: Time-based rainbow lights."""
import asyncio
import aioconsole
import colorsys
from intelino.trainlib_async import TrainScanner, Train


async def waiter(event: asyncio.Event):
    # let the program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit...")
    event.set()


async def rainbow_lights(train: Train):
    # make sure our rainbow colors are not interrupted by other animations
    await train.set_snap_command_feedback(sound=True, lights=False)

    rainbow_steps = 360  # as degrees on the (hue) color wheel
    rainbow_duration = 5.0  # seconds

    exit_event = asyncio.Event()
    asyncio.create_task(waiter(exit_event))

    rainbow_position = 0
    while not exit_event.is_set():
        # convert HSV rainbow to RGB
        rgb_coordinate = colorsys.hsv_to_rgb(rainbow_position / rainbow_steps, 1, 1)
        # scale RGB values to bytes
        rgb_bytes = tuple(int(255 * val) for val in rgb_coordinate)

        await train.set_top_led_color(*rgb_bytes)
        await asyncio.sleep(rainbow_duration / rainbow_steps)

        # advance rainbow position
        rainbow_position = (rainbow_position + 1) % rainbow_steps

    # cleanup
    await train.set_top_led_color(0, 0, 0)
    await train.set_snap_command_feedback(sound=True, lights=True)


async def main():
    async with TrainScanner() as train:
        # run our train program
        await rainbow_lights(train)


if __name__ == "__main__":
    asyncio.run(main())
