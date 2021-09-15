"""Data stream example (2): Throttle/sample a fast stream in periodic time
intervals.

Note: The ReactiveX operator `sample` / `throttle_last` is used in this example.
All the other `throttle*` operators are synonyms to the `debounce` operator,
which is not applicable for this situation.
"""
import asyncio
import aioconsole
from rx import operators as ops
from rx.scheduler.eventloop import AsyncIOScheduler
from intelino.trainlib_async import TrainScanner, Train, TrainMsgMovement
from intelino.trainlib_async.helpers import AsyncObserver


async def data_streams(train: Train):
    """
    Print current speed every 5 seconds and desired speed as soon as it changes.
    """

    async def print_speed(msg: TrainMsgMovement):
        print(f"Current speed: {msg.speed_cmps} cm/s")

    async def print_change(msg: TrainMsgMovement):
        print(f"Desired speed changed to: {msg.desired_speed_cmps} cm/s")

    # enable the movement notification stream
    # Note: we want it as fast as possible this time
    movement_stream = await train.movement_notification_stream(
        streaming=True,
        interval=0.100,  # 100 ms is the fastest (and default)
    )

    # make sure we use an asyncio scheduler for our Rx stream
    scheduler = AsyncIOScheduler(asyncio.get_event_loop())

    subscription1 = movement_stream.pipe(
        # sample our 100ms stream every 5 seconds
        ops.sample(5.0, scheduler=scheduler),
    ).subscribe(AsyncObserver(print_speed))

    subscription2 = movement_stream.pipe(
        # compare desired speed values and emit only if the value changed
        ops.distinct_until_changed(lambda msg: msg.desired_speed_cmps)
    ).subscribe(AsyncObserver(print_change))

    # start driving
    await train.drive_at_speed(35)

    # let the train program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")

    # cleanup
    subscription1.dispose()
    subscription2.dispose()
    await train.stop_driving()


async def main():
    async with TrainScanner() as train:
        # run our train program
        await data_streams(train)


if __name__ == "__main__":
    asyncio.run(main())
