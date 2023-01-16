"""Data stream example (1): Print speed every 5 seconds."""
import asyncio
import aioconsole
from intelino.trainlib_async import TrainScanner, Train
from intelino.trainlib_async.messages import TrainMsgMovement
from intelino.trainlib_async.helpers import AsyncObserver


async def data_streams(train: Train):
    """
    Print current (and desired) speed every 5 seconds.
    """

    async def movement_observer_func(msg: TrainMsgMovement):
        print(
            f"Set speed: {msg.desired_speed_cmps} cm/s",
            f"Current speed: {msg.speed_cmps} cm/s",
        )

    # enable the movement notification stream every 5 seconds
    # Note: since we use it only for one purpose, we can do this
    movement_stream = await train.movement_notification_stream(
        streaming=True,
        interval=5.0,
    )
    subscription = movement_stream.subscribe(AsyncObserver(movement_observer_func))

    # start driving
    await train.drive_at_speed(35)

    # let the train program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")

    # cleanup
    subscription.dispose()
    await train.stop_driving()


async def main():
    async with TrainScanner() as train:
        # run our train program
        await data_streams(train)


if __name__ == "__main__":
    asyncio.run(main())
