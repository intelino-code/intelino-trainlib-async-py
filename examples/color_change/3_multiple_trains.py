"""Color change event example (3): Run same code on multiple trains."""
import asyncio
import aioconsole
from intelino.trainlib_async import (
    TrainScanner,
    Train,
    TrainMsg,
    TrainMsgEventFrontColorChanged,
)


async def waiter(event: asyncio.Event):
    # let the train program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")
    event.set()


async def color_change(train: Train, index: int, exit_event: asyncio.Event):
    """
    Wait for color change events and set headlights/taillights
    based on the seen color.
    """

    def observer_func(msg: TrainMsg):
        if isinstance(msg, TrainMsgEventFrontColorChanged):
            print(f"New color on train {index}: {msg.color}")
            color = msg.color.to_rgb_bytes()
            asyncio.create_task(train.set_headlight_color(color, color))

    # subscribe to the notification stream
    subscription = train.notifications.subscribe(observer_func)

    # wait for the exit event to happen
    await exit_event.wait()

    # cleanup
    subscription.dispose()


async def main():
    # connect to the first 2 trains discovered
    trains = await TrainScanner().get_trains(count=2)
    exit_event = asyncio.Event()

    # run our train program with all our trains
    await asyncio.gather(
        waiter(exit_event),
        *(color_change(train, idx, exit_event) for idx, train in enumerate(trains)),
    )
    # after the program finished, disconnect from the trains
    for train in trains:
        await train.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
