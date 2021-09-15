"""Color change event example (4):
    Share the latest seen color with all trains (any to all).
    In this example we use a callback function to achieve this.
"""
import asyncio
import aioconsole
from typing import Any, Callable, Coroutine, List
from intelino.trainlib_async import (
    TrainScanner,
    Train,
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
    set_headlights: Callable[[SnapColorValue], Coroutine[Any, Any, None]],
    exit_event: asyncio.Event,
):
    """
    Wait for color change events and set headlights/taillights
    based on the seen color using the provided callback function.
    """

    def observer_func(msg: TrainMsg):
        if isinstance(msg, TrainMsgEventFrontColorChanged):
            print(f"New color on train {index}: {msg.color}")
            if msg.color not in (SnapColorValue.BLACK, SnapColorValue.UNKNOWN):
                asyncio.create_task(set_headlights(msg.color))

    # subscribe to the notification stream
    subscription = train.notifications.subscribe(observer_func)

    # wait for the exit event to happen
    await exit_event.wait()

    # cleanup
    subscription.dispose()


def build_headlights_callback(trains: List[Train]):
    """Build a callback function that will be able to update all the trains."""

    async def set_headlights_on_all_trains(color: SnapColorValue):
        rgb = color.to_rgb_bytes()
        await asyncio.gather(
            *(train.set_headlight_color(rgb, rgb) for train in trains),
        )

    # return and async function that sets headlights on all the trains
    return set_headlights_on_all_trains


async def main():
    # connect to the first 2 trains discovered
    trains = await TrainScanner().get_trains(count=2)
    exit_event = asyncio.Event()
    set_headlights_callback = build_headlights_callback(trains)

    # run our train program with all our trains
    await asyncio.gather(
        waiter(exit_event),
        *(
            color_change(train, idx, set_headlights_callback, exit_event)
            for idx, train in enumerate(trains)
        ),
    )

    # after the program finished, disconnect from the trains
    for train in trains:
        await train.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
