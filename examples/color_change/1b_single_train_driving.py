"""Color change event example (1b): Single train driving."""
import asyncio
import aioconsole
from intelino.trainlib_async import (
    TrainScanner,
    Train,
    TrainMsg,
    TrainMsgEventFrontColorChanged,
    TrainMsgEventBackColorChanged,
    TrainMsgEventMovementDirectionChanged,
)
from intelino.trainlib_async.enums import SnapColorValue, MovementDirection


async def color_change(train: Train):
    """
    Wait for color change events and set headlights/taillights
    based on the seen color on the front sensor relative to the driving
    direction.
    """
    # train's local state
    drive_direction: MovementDirection = MovementDirection.STOP

    async def new_color(color: SnapColorValue):
        if color not in (SnapColorValue.BLACK, SnapColorValue.UNKNOWN):
            # ignore black and unknown
            print(f"New color: {color}")
            rgb = color.to_rgb_bytes()
            await train.set_headlight_color(rgb, rgb)

    def observer_func(msg: TrainMsg):
        nonlocal drive_direction

        if isinstance(msg, TrainMsgEventMovementDirectionChanged):
            # update state only
            drive_direction = msg.direction

        elif isinstance(msg, TrainMsgEventFrontColorChanged):
            if drive_direction != MovementDirection.BACKWARD:
                # accept forward and stopped directions
                asyncio.create_task(new_color(msg.color))

        elif isinstance(msg, TrainMsgEventBackColorChanged):
            if drive_direction == MovementDirection.BACKWARD:
                asyncio.create_task(new_color(msg.color))

    # subscribe to the notification stream
    subscription = train.notifications.subscribe(observer_func)

    # start driving
    await train.drive_at_speed(35)

    # let the train program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")

    # cleanup
    subscription.dispose()
    await train.stop_driving()
    await train.set_headlight_color()


async def main():
    async with TrainScanner() as train:
        # run our train program
        await color_change(train)


if __name__ == "__main__":
    asyncio.run(main())
