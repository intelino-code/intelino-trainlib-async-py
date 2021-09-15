"""Example: Overriding built-in snap commands.

Here we demonstrate how the most common built-in snaps could
be mimicked in a remotely running code executed over Bluetooth LE.
Due to communication lag, it will never match the reaction speed
and precision of the built-in commands. For example, steering
on a split track (switch) is too slow to be done over BLE as
a snap detection callback.

"""

import asyncio
from intelino.trainlib_async.enums.enums import MovementDirection, SpeedLevel
from intelino.trainlib_async.helpers import AsyncObserver
import aioconsole
from intelino.trainlib_async import (
    TrainScanner,
    Train,
    TrainMsg,
    TrainMsgEventSnapCommandDetected,
)

# import SnapColorValue with a shorter name for convenience
from intelino.trainlib_async.enums import SnapColorValue as C


async def snap_commands(train: Train):
    """
    Disable built-in snap execution and handle detected snap events
    with custom code in python.
    """

    async def observer_func(msg: TrainMsg):
        if isinstance(msg, TrainMsgEventSnapCommandDetected):
            # every white/cyan snap starts the snap command detection
            print(f"Detected a snap with colors: {tuple(map(str, msg.colors))}")

            if msg.colors == (C.WHITE, C.GREEN, C.GREEN, C.GREEN):
                await train.drive_at_speed_level(
                    SpeedLevel.LEVEL3, MovementDirection.CURRENT
                )

            elif msg.colors == (C.WHITE, C.GREEN, C.GREEN, C.BLACK):
                await train.drive_at_speed_level(
                    SpeedLevel.LEVEL2, MovementDirection.CURRENT
                )

            elif msg.colors == (C.WHITE, C.GREEN, C.BLACK, C.BLACK):
                await train.drive_at_speed_level(
                    SpeedLevel.LEVEL1, MovementDirection.CURRENT
                )

            elif msg.colors == (C.WHITE, C.RED, C.RED, C.RED):
                await train.pause_driving(10.0)

            elif msg.colors == (C.WHITE, C.RED, C.RED, C.BLACK):
                await train.pause_driving(5.0)

            elif msg.colors == (C.WHITE, C.RED, C.BLACK, C.BLACK):
                await train.pause_driving(2.0)

            elif msg.colors == (C.WHITE, C.BLUE, C.BLACK, C.BLACK):
                # to reverse, we need to know the speed
                msg = await train.get_movement_notification()
                await train.drive_at_speed(
                    msg.desired_speed_cmps, MovementDirection.INVERT
                )

            elif msg.colors == (C.WHITE, C.YELLOW, C.BLACK, C.BLACK):
                await train.decouple_wagon()

    # subscribe to the notification stream
    subscription = train.notifications.subscribe(AsyncObserver(observer_func))

    # disable all snap commands
    # including splits (cyan) and custom snap commands (white-magenta)
    await train.set_snap_command_execution(False)

    # start driving
    await train.drive_at_speed(35)

    # let the train program run until the 'enter' key is pressed
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")

    # cleanup
    subscription.dispose()
    await train.stop_driving()
    await train.set_snap_command_execution(True)


async def main():
    async with TrainScanner() as train:
        # run our train program
        await snap_commands(train)


if __name__ == "__main__":
    asyncio.run(main())
