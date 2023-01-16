"""Color change event example (2): Single leader and multiple follower trains."""
import asyncio
import aioconsole
from typing import List
from intelino.trainlib_async import (
    TrainScanner,
    Train,
)
from intelino.trainlib_async.messages import (
    TrainMsg,
    TrainMsgEventFrontColorChanged,
)


async def color_change(leader: Train, followers: List[Train]):
    """
    Wait for color change events on the leader train and set
    headlights/taillights based on the seen color on all the trains.
    """

    def observer_func(msg: TrainMsg):
        if isinstance(msg, TrainMsgEventFrontColorChanged):
            print(f"New color: {msg.color}")
            color = msg.color.to_rgb_bytes()
            asyncio.create_task(leader.set_headlight_color(color, color))
            for follower in followers:
                asyncio.create_task(follower.set_headlight_color(color, color))

    # subscribe to the notification stream
    subscription = leader.notifications.subscribe(observer_func)

    # highlight the leader train
    await leader.set_top_led_color(0, 255, 0)

    # let the train program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")

    # cleanup
    subscription.dispose()


async def main():
    # connect to the first 3 trains discovered
    trains = await TrainScanner().get_trains(count=3)

    # run our train program
    await color_change(trains[0], trains[1:])
    # after the program finished, disconnect from the trains
    for train in trains:
        await train.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
