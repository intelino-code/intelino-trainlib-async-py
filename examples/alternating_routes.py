"""Example: Alternating routes (left/right) - async version."""
import asyncio
import aioconsole
from intelino.trainlib_async import (
    TrainScanner,
    Train,
)
from intelino.trainlib_async.messages import (
    TrainMsg,
    TrainMsgEventSnapCommandDetected,
)
from intelino.trainlib_async.enums import SteeringDecision, SnapColorValue


async def set_decision(train: Train, split_counter: int):
    """Pick a side based on the split counter."""
    if split_counter % 2 == 0:
        side = SteeringDecision.RIGHT
        color = (0, 0, 255)  # blue
    else:
        side = SteeringDecision.LEFT
        color = (255, 0, 0)  # red

    print(f"Next {repr(side)}, splits seen: {split_counter}")
    await train.set_next_split_steering_decision(side)
    await train.set_headlight_color(color, color)


def is_split_track_snap(msg: TrainMsgEventSnapCommandDetected):
    """Helper function to identify split track snaps."""
    return (msg.colors[0] == SnapColorValue.CYAN) and (
        msg.colors[1] != SnapColorValue.BLACK
    )


async def alternating_routes(train: Train):
    """Alternate between left and right turns."""
    split_counter = 0

    def observer_func(msg: TrainMsg):
        nonlocal split_counter

        if isinstance(msg, TrainMsgEventSnapCommandDetected) and is_split_track_snap(
            msg
        ):
            # we are on a split track (identified by its snaps)
            split_counter += 1
            asyncio.create_task(set_decision(train, split_counter))

    # subscribe to the notification stream
    subscription = train.notifications.subscribe(observer_func)

    await set_decision(train, split_counter)
    await train.drive_at_speed(40)

    # let the train run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")

    # cleanup
    subscription.dispose()
    await train.stop_driving()


async def main():
    async with TrainScanner() as train:
        # run our train program
        await alternating_routes(train)


if __name__ == "__main__":
    asyncio.run(main())
