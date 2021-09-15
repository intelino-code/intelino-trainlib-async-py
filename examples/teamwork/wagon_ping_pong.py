"""Teamwork example: Wagon hand-over for 2 trains.

Track requirements:
- track with an inner and outer loop
- snaps:
  - white-magenta: double sided snap command for wagon drop off and pickup
      on both inner loop sides
  - white-magenta-red: waiting state on the outer loops
      on both outer loop sides
  - white-magenta-blue: reversing maneuver for wagon pickup
      between the split tracks

"""
import asyncio
import aioconsole
from enum import Enum
from rx import operators as ops
from rx.core.typing import Disposable
from rx.subject import BehaviorSubject
from rx.scheduler.eventloop import AsyncIOScheduler
from typing import List, NamedTuple
from intelino.trainlib_async import (
    TrainScanner,
    Train,
    TrainMsgEventSnapCommandDetected,
)
from intelino.trainlib_async.enums import (
    SnapColorValue as Color,
    MovementDirection,
    SteeringDecision,
)
from intelino.trainlib_async.helpers import AsyncObserver

#
# Data types
#

WagonState = Enum("WagonState", "UNKNOWN CARRIED_BY READY_FOR")


class WagonInfo(NamedTuple):
    state: WagonState
    train_id: int


class SharedState:
    def __init__(self):
        self.exit_event = asyncio.Event()
        # wagon info stream to notify other trains when ready for pickup
        self.wagon = BehaviorSubject(WagonInfo(WagonState.UNKNOWN, -1))

    def dispose(self):
        self.wagon.on_completed()
        self.wagon.dispose()


class LocalState:
    def __init__(self):
        # waiting for the wagon to be ready for us
        self.waiting = True
        # when carrying the wagon, we need to pass a checkpoint before drop off
        # is allowed
        self.checkpoint_passed = False


#
# Functions
#


async def waiter(event: asyncio.Event):
    """Let the train program run until the 'enter' key is pressed."""
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")
    event.set()


async def starter(shared_state: SharedState):
    """Since we connect to random (unnamed) trains, we need to manually give
    the wagon to the "first" train (glowing green).
    """
    print("Attach the wagon to the train that glows GREEN.")
    await asyncio.sleep(1.0)
    await aioconsole.ainput("Press <Enter> when ready to start...\n")
    # notify the train that it has the wagon
    shared_state.wagon.on_next(WagonInfo(WagonState.CARRIED_BY, 0))
    await asyncio.sleep(1.0)
    await waiter(shared_state.exit_event)


async def wagon_ping_pong(train: Train, index: int, shared_state: SharedState):
    """Two trains exchange a wagon."""
    state = LocalState()

    async def milestone(msg: TrainMsgEventSnapCommandDetected):
        if msg.colors == (Color.WHITE, Color.MAGENTA, Color.BLACK, Color.BLACK):
            # inner loop - wagon exchange place
            if (
                shared_state.wagon.value == (WagonState.CARRIED_BY, index)
            ) and state.checkpoint_passed:
                # drop off
                await train.decouple_wagon()
                # inform the other trains of the wagon being ready for them
                shared_state.wagon.on_next(
                    WagonInfo(WagonState.READY_FOR, (index + 1) % 2)
                )
                # navigate home
                await train.set_next_split_steering_decision(SteeringDecision.STRAIGHT)

            elif shared_state.wagon.value == (WagonState.READY_FOR, index):
                # pickup
                # "hope" that we attached the wagon
                state.checkpoint_passed = False
                await train.drive_at_speed(40, MovementDirection.FORWARD)
                await train.set_next_split_steering_decision(SteeringDecision.LEFT)
                shared_state.wagon.on_next(WagonInfo(WagonState.CARRIED_BY, index))

        elif msg.colors.start_with(Color.WHITE, Color.MAGENTA, Color.RED):
            # outer loop - resting place
            if shared_state.wagon.value.train_id != index:
                # wagon is not ours (nor carried by nor ready for us)
                state.waiting = True
                await train.stop_driving()

        elif msg.colors.start_with(Color.WHITE, Color.MAGENTA, Color.BLUE):
            # middle section - checkpoint
            if shared_state.wagon.value == (WagonState.CARRIED_BY, index):
                state.checkpoint_passed = True

            elif shared_state.wagon.value == (WagonState.READY_FOR, index):
                # reverse for pickup
                await train.drive_at_speed(30, MovementDirection.BACKWARD)
                await train.set_next_split_steering_decision(SteeringDecision.RIGHT)

    async def wagon_ready(info: WagonInfo):
        if (info == (WagonState.READY_FOR, index)) and state.waiting:
            # the wagon is ready for us
            state.waiting = False
            await train.drive_at_speed(40)

        elif (info == (WagonState.CARRIED_BY, index)) and state.waiting:
            # the wagon is attached to us on game start
            state.waiting = False
            await train.drive_at_speed(40)
            await train.set_next_split_steering_decision(SteeringDecision.LEFT)

    # create a list of subscriptions
    subscriptions: List[Disposable] = []

    # make sure we use an asyncio scheduler for our Rx stream
    asyncio_scheduler = AsyncIOScheduler(asyncio.get_event_loop())

    sub = train.notifications.pipe(
        # we are interested only in snap events, so we filter the stream
        ops.filter(lambda msg: isinstance(msg, TrainMsgEventSnapCommandDetected)),
        ops.filter(lambda msg: msg.colors.start_with(Color.WHITE, Color.MAGENTA)),
        # Corner case: reversing at high speeds might "phantom-detect"
        # the same or partial snap command due to wheel slippage
        ops.throttle_first(0.8, scheduler=asyncio_scheduler),
    ).subscribe(AsyncObserver(milestone))
    subscriptions.append(sub)

    sub = shared_state.wagon.subscribe(AsyncObserver(wagon_ready))
    subscriptions.append(sub)

    # clear all custom snap commands stored on the train (just to be sure)
    await train.clear_custom_snap_commands()
    # disable built-in snap commands to avoid any interference with our program
    await train.set_snap_command_execution(False)

    if index == 0:
        # the "first" train to have the wagon should glow green
        await train.set_top_led_color(0, 255, 0)

    # wait for the exit event to happen
    await shared_state.exit_event.wait()

    # cleanup
    for subscription in subscriptions:
        subscription.dispose()
    await train.stop_driving()
    await train.set_snap_command_execution(True)


async def main():
    # connect to the first 2 trains discovered
    trains = await TrainScanner().get_trains(count=2)
    shared_state = SharedState()

    # run our train program with all our trains
    await asyncio.gather(
        starter(shared_state),
        *(
            wagon_ping_pong(train, idx, shared_state)
            for idx, train in enumerate(trains)
        ),
    )

    # after the program finished, clean up and disconnect from the trains
    shared_state.dispose()
    for train in trains:
        await train.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
