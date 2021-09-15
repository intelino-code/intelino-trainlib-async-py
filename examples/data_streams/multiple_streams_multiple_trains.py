"""Data stream example (3): Subscribe to multiple streams.

Listen and print:
- current speed every 5 seconds
- desired speed as soon as it changes
- type of the split track (switch) when we cross it

Listen and do:
- change headlights and taillights every 2 seconds (randomly)

Listen and do on all trains:
- on white-magenta snap give the train a speed boost for 1 seconds

Train 0 specific:
- on white-magenta snap instead of boost, pause all trains for 2 seconds
- headlights and taillights are not random to allow identification

"""
import asyncio
import aioconsole
import rx
from rx import operators as ops
from rx.core.typing import Disposable
from rx.subject.subject import Subject
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


async def waiter(event: asyncio.Event):
    # let the train program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")
    event.set()


async def data_streams(
    train: Train,
    index: int,
    shared_events: Subject,  # type: Subject[str]
    exit_event: asyncio.Event,
):
    """
    Configure and subscribe to multiple streams on multiple trains.
    While most of the train program is simmilar, introduce some exceptions
    to train 0 (first connected train).

    Since we need to do multiple timed actions which interfere in nature,
    boosting (1s) and pausing (2s), we need to introduce some "state", that
    would prevent issues when we want to pause during a boost (or vice versa).
    We decided, that pausing will have a precedence over boosting.
    Note: The boosting time is controlled by the python code (via sleep), while
    the pausing time is controlled by the train.
    """
    boosted: bool = False
    paused: bool = False
    preboost_speed: float = 0

    async def print_speed(msg: TrainMsgMovement):
        print(f"Train {index}: Current speed: {msg.speed_cmps} cm/s")

    async def print_change(msg: TrainMsgMovement):
        print(f"Train {index}: Desired speed changed to: {msg.desired_speed_cmps} cm/s")

    async def print_switch_type(msg: TrainMsgEventSnapCommandDetected):
        if msg.colors[0] == Color.CYAN:
            # only split tracks start with cyan
            if msg.colors[1] == Color.RED:
                print(f"Train {index}: Switch with a branch on left.")
            if msg.colors[1] == Color.BLUE:
                print(f"Train {index}: Switch with a branch on right.")
            if msg.colors[1] == Color.BLACK:
                print(f"Train {index}: Switch in a merging direction.")

    async def white_magenta(msg: TrainMsgEventSnapCommandDetected):
        if msg.colors == (Color.WHITE, Color.MAGENTA, Color.BLACK, Color.BLACK):
            if index == 0:
                # train with index 0 pauses all trains instead of boosting
                shared_events.on_next("PAUSE")
            else:
                shared_events.on_next("BOOST")

    async def speed_boost():
        """since we need to do multiple timed actions (boosting and pausing)
        this code had to change to accomodate the conflicting nature of those
        two actions
        """
        nonlocal boosted, paused, preboost_speed

        movement_info = await train.get_movement_notification()
        speed = movement_info.desired_speed_cmps

        if boosted:  # prevent boosting twice
            print(f"Train {index}: Boost already running.")
            return

        if paused or (movement_info.pause_time_ms > 0):
            # prevent boosting during a pause (very rare)
            print(f"Train {index}: Boost skipped due to pausing.")
            return

        preboost_speed = speed
        boosted = True
        print(f"Train {index}: Boosting +50% for 1 seconds...")
        await train.drive_at_speed(speed * 1.5, MovementDirection.CURRENT)
        await asyncio.sleep(1)
        if boosted and not paused:
            # during the sleep time, boost could have been cancelled by the
            # pause action
            await train.drive_at_speed(speed, MovementDirection.CURRENT)
            boosted = False

    async def pause():
        nonlocal boosted, paused, preboost_speed

        # update local state before the train starts streaming its pause time
        paused = True
        if boosted:
            # we need to cancel the boost and restore the pre-boost speed
            # before pausing
            await train.drive_at_speed(preboost_speed, MovementDirection.CURRENT)
            boosted = False

        await train.pause_driving(2.0)
        # even though pause is still on, we set the local state to False, as
        # the pause timing is controlled by the train
        paused = False

    async def update_headlights(i: int):
        if index == 0:
            # train with index 0 should be distinguishable from the others
            colors = (Color.RED.to_rgb_bytes(), Color.BLUE.to_rgb_bytes())
            # swap red/blue on front/back every iteration
            await train.set_headlight_color(colors[i % 2], colors[(i + 1) % 2])
        else:
            # the other trains remain random
            rgb = Color.random().to_rgb_bytes()
            await train.set_headlight_color(rgb, rgb)

    async def shared_logic(cmd: str):
        if cmd == "PAUSE":
            await pause()

        elif cmd == "BOOST":
            await speed_boost()

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
    sub = snap_stream.subscribe(AsyncObserver(white_magenta))
    subscriptions.append(sub)

    time_stream = rx.interval(2.0, asyncio_scheduler)
    sub = time_stream.subscribe(AsyncObserver(update_headlights))
    subscriptions.append(sub)

    # subscribe to our program's stream
    sub = shared_events.subscribe(AsyncObserver(shared_logic))
    subscriptions.append(sub)

    # start driving
    await train.drive_at_speed(35)

    # wait for the exit event to happen
    await exit_event.wait()

    # cleanup
    for subscription in subscriptions:
        subscription.dispose()
    await train.stop_driving()
    await train.set_headlight_color()


async def main():
    # connect to the first 2 trains discovered
    trains = await TrainScanner().get_trains(count=2)
    exit_event = asyncio.Event()
    # create a shared event stream to exchange data/commands (in this case
    # string commands "PAUSE" or "BOOST") between all train programs
    # Note: in bigger programs this would be an enum (instead of string)
    shared_events = Subject()  # type: Subject[str]

    # run our train program with all our trains
    await asyncio.gather(
        waiter(exit_event),
        *(
            data_streams(train, idx, shared_events, exit_event)
            for idx, train in enumerate(trains)
        ),
    )

    # after the program finished, clean up and disconnect from the trains
    shared_events.on_completed()
    shared_events.dispose()
    for train in trains:
        await train.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
