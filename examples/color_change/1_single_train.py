"""Color change event example (1): Single train."""
import asyncio
import aioconsole
from intelino.trainlib_async import (
    TrainScanner,
    Train,
)
from intelino.trainlib_async.messages import (
    TrainMsg,
    TrainMsgEventFrontColorChanged,
)


async def color_change(train: Train):
    """
    Wait for color change events and set headlights/taillights
    based on the seen color.
    """

    def observer_func(msg: TrainMsg):
        if isinstance(msg, TrainMsgEventFrontColorChanged):
            print(f"New color: {msg.color}")
            color = msg.color.to_rgb_bytes()
            asyncio.create_task(train.set_headlight_color(color, color))

    # subscribe to the notification stream
    subscription = train.notifications.subscribe(observer_func)

    # let the train program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")

    # cleanup
    subscription.dispose()


async def main():
    async with TrainScanner() as train:
        # run our train program
        await color_change(train)


if __name__ == "__main__":
    asyncio.run(main())
