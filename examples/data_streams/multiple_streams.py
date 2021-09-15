"""Data stream example (3): Subscribe to multiple streams.

Listen and print:
- current speed every 5 seconds
- desired speed as soon as it changes
- type of the split track (switch) when we cross it

Listen and do:
- on white-magenta snap give the train a speed boost for 1 seconds
- change headlights and taillights every 2 seconds (randomly)

"""
import asyncio
import aioconsole
import rx
from rx import operators as ops
from rx.core.typing import Disposable
from rx.scheduler.eventloop import AsyncIOScheduler
from typing import List
from intelino.trainlib_async import (
    TrainScanner,
    Train,
    TrainMsgMovement,
    TrainMsgEventSnapCommandDetected,
)
from intelino.trainlib_async.enums import SnapColorValue as Color, MovementDirection
from intelino.trainlib_async.helpers import AsyncObserver


async def data_streams(train: Train):
    """
    Configure and subscribe to multiple streams.
    """

    async def print_speed(msg: TrainMsgMovement):
        print(f"Current speed: {msg.speed_cmps} cm/s")

    async def print_change(msg: TrainMsgMovement):
        print(f"Desired speed changed to: {msg.desired_speed_cmps} cm/s")

    async def print_switch_type(msg: TrainMsgEventSnapCommandDetected):
        if msg.colors[0] == Color.CYAN:
            # only split tracks start with cyan
            if msg.colors[1] == Color.RED:
                print("Switch with a branch on left.")
            if msg.colors[1] == Color.BLUE:
                print("Switch with a branch on right.")
            if msg.colors[1] == Color.BLACK:
                print("Switch in a merging direction.")

    async def speed_boost(msg: TrainMsgEventSnapCommandDetected):
        if msg.colors == (Color.WHITE, Color.MAGENTA, Color.BLACK, Color.BLACK):
            if hasattr(speed_boost, "running") and speed_boost.running:
                # prevent boosting twice with a "static" function attribute
                print("Boost already running.")
                return

            speed_boost.running = True
            movement_info = await train.get_movement_notification()
            speed = movement_info.desired_speed_cmps
            print("Boosting +50% for 1 seconds...")
            await train.drive_at_speed(speed * 1.5, MovementDirection.CURRENT)
            await asyncio.sleep(1)
            await train.drive_at_speed(speed, MovementDirection.CURRENT)
            speed_boost.running = False

    async def update_headlights(i: int):
        rgb = Color.random().to_rgb_bytes()
        await train.set_headlight_color(rgb, rgb)

    # create a list of subscriptions
    # Note: since we don't need to unsubscribe individually, we can dispose
    # all subscriptions through a list.
    subscriptions: List[Disposable] = []

    # enable the movement notification stream
    # Note: we want it as fast as possible this time
    movement_stream = await train.movement_notification_stream(
        streaming=True,
        interval=0.100,  # 100 ms is the fastest (and default)
    )

    # make sure we use an asyncio scheduler for our Rx stream
    asyncio_scheduler = AsyncIOScheduler(asyncio.get_event_loop())

    sub = movement_stream.pipe(
        # sample our 100ms stream every 5 seconds
        ops.sample(5.0, scheduler=asyncio_scheduler),
    ).subscribe(AsyncObserver(print_speed))
    subscriptions.append(sub)

    sub = movement_stream.pipe(
        # compare desired speed values and emit only if the value changed
        ops.distinct_until_changed(lambda msg: msg.desired_speed_cmps)
    ).subscribe(AsyncObserver(print_change))
    subscriptions.append(sub)

    snap_stream = train.notifications.pipe(
        # we are interested only in snap events, so we filter the stream
        ops.filter(lambda msg: isinstance(msg, TrainMsgEventSnapCommandDetected))
    )
    sub = snap_stream.subscribe(AsyncObserver(print_switch_type))
    subscriptions.append(sub)
    sub = snap_stream.subscribe(AsyncObserver(speed_boost))
    subscriptions.append(sub)

    time_stream = rx.interval(2.0, asyncio_scheduler)
    sub = time_stream.subscribe(AsyncObserver(update_headlights))
    subscriptions.append(sub)

    # start driving
    await train.drive_at_speed(35)

    # let the train program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")

    # cleanup
    for subscription in subscriptions:
        subscription.dispose()
    await train.stop_driving()
    await train.set_headlight_color()


async def main():
    async with TrainScanner() as train:
        # run our train program
        await data_streams(train)


if __name__ == "__main__":
    asyncio.run(main())
