import asyncio
import random
from intelino.trainlib_async import Train, TrainMsg
from intelino.trainlib_async.train_factory import TrainFactory
from intelino.trainlib_async.enums import SpeedLevel


async def train_program(train: Train):
    print(f"starting train program {train.id}")

    def callback(data: TrainMsg):
        print(train.id, data)

    subscription = train.notifications.subscribe(callback)

    try:
        print("drive medium speed forward")
        await train.drive_at_speed_level(SpeedLevel.LEVEL2)

        for _ in range(10):
            print("setting color...")
            color = [random.randint(0, 1) * 0xFF for i in range(3)]
            await train.set_headlight_color(front=color, back=color)
            await asyncio.sleep(1.0)

        subscription.dispose()

        print("stop movement")
        await train.stop_driving()

        print(f"disconnecting from {train.id}")
        await train.disconnect()

    except Exception as e:
        print(e)


async def main():
    # Note: in case we would need to connect to specific trains, we can do that too.
    # addresses = [
    #     "33AA542E-1452-4525-8DB8-7BC941A7FE49",
    #     "CD3C3305-36E2-4DE7-94F3-EC7FFF59E1F8",
    # ]
    # trains = [await TrainFactory.create_train(address, timeout=5.0) for address in addresses]
    # trains = list(filter(None, trains))

    # connect to the first 2 trains discovered
    trains = await TrainFactory.create_trains(count=2, timeout=5.0)

    await asyncio.gather(*(train_program(train) for train in trains))


if __name__ == "__main__":
    asyncio.run(main())
