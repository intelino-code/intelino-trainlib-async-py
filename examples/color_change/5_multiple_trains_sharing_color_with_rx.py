"""Color change event example (5):
    Share the latest seen color with all trains (any to all).
    In this example we use ReactiveX (RxPY).
"""
import asyncio
import aioconsole
from rx.subject.subject import Subject
from intelino.trainlib_async import (
    TrainScanner,
    Train,
)
from intelino.trainlib_async.messages import (
    TrainMsg,
    TrainMsgEventFrontColorChanged,
)
from intelino.trainlib_async.enums import SnapColorValue


async def waiter(event: asyncio.Event):
    # let the train program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")
    event.set()


async def color_change(
    train: Train,
    index: int,
    shared_events: Subject,  # type: Subject[SnapColorValue]
    exit_event: asyncio.Event,
):
    """
    Wait for color change events, signal colors through the shared
    event-stream, set headlights/taillights based on the shared event-stream.
    """

    def train_observer_func(msg: TrainMsg):
        """Handle color detection coming from the train."""
        if isinstance(msg, TrainMsgEventFrontColorChanged):
            print(f"New color on train {index}: {msg.color}")
            if msg.color not in (SnapColorValue.BLACK, SnapColorValue.UNKNOWN):
                # forward the color to all trains
                shared_events.on_next(msg.color)

    # subscribe to train notifications
    subs_train = train.notifications.subscribe(train_observer_func)

    def shared_stream_observer_func(color: SnapColorValue):
        """Update color based on the shared event/command stream."""
        rgb = color.to_rgb_bytes()
        asyncio.create_task(train.set_headlight_color(rgb, rgb))

    # subscribe to our program's stream
    subs_program = shared_events.subscribe(shared_stream_observer_func)

    # wait for the exit event to happen
    await exit_event.wait()

    # cleanup
    subs_program.dispose()
    subs_train.dispose()


async def main():
    # connect to the first 2 trains discovered
    trains = await TrainScanner().get_trains(count=2)
    exit_event = asyncio.Event()
    # create a shared event stream to exchange data/commands (in this case
    # just color) between all the train programs
    shared_events = Subject()  # type: Subject[SnapColorValue]

    # run our train program with all our trains
    await asyncio.gather(
        waiter(exit_event),
        *(
            color_change(train, idx, shared_events, exit_event)
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
