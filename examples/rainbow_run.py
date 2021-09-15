"""Example: Distance-based rainbow lights."""
import asyncio
import aioconsole
import colorsys
from intelino.trainlib_async import TrainScanner, Train
from intelino.trainlib_async.enums import MovementDirection
from intelino.trainlib_async.messages import TrainMsgMovement


async def rainbow_run(train: Train):
    odometer_on_start = 0

    # make sure our rainbow colors are not interrupted by other animations
    await train.set_snap_command_feedback(sound=True, lights=False)

    movement_msg = await train.get_movement_notification()
    odometer_on_start = movement_msg.lifetime_odometer_meters

    async def set_color_based_on_distance(distance_meters: float):
        distance_cm = distance_meters * 100

        # let 1 rainbow be 100 cm
        rainbow_length = 100
        rainbow_position = distance_cm % rainbow_length

        # convert HSV rainbow to RGB
        rgb_coordinate = colorsys.hsv_to_rgb(rainbow_position / rainbow_length, 1, 1)
        # scale RGB values to bytes
        rgb_bytes = tuple(int(255 * val) for val in rgb_coordinate)

        await train.set_top_led_color(*rgb_bytes)

    def notification_handler(movement_msg: TrainMsgMovement):
        distance_meters = movement_msg.lifetime_odometer_meters - odometer_on_start
        asyncio.create_task(set_color_based_on_distance(distance_meters))

    # subscribe to the train's movement notification stream
    stream = await train.movement_notification_stream(streaming=True)
    subscription = stream.subscribe(notification_handler)

    await train.drive_at_speed(
        speed_cmps=35, direction=MovementDirection.FORWARD, play_feedback=False
    )

    # let the train run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit...")

    # cleanup
    subscription.dispose()
    await train.stop_driving()
    await train.set_top_led_color(0, 0, 0)
    await train.set_snap_command_feedback(sound=True, lights=True)


async def main():
    async with TrainScanner() as train:
        # run our train program
        await rainbow_run(train)


if __name__ == "__main__":
    asyncio.run(main())
