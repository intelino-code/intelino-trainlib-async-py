"""Teamwork example: Collision avoidance (v1) for two trains.

Track requirements:
- Double loop (inner + outer) with two "shared" sections
  - outer loop is clockwise
  - inner loop is counter-clockwise
- Yellow and magenta snaps are used to identify the shared sections.

Notes (corner cases):
- When the critical section is freed, all waiting trains are allowed to enter.
  That means this example code works only when there is exactly one train
  waiting.

"""
import asyncio
import aioconsole
from enum import Enum
from rx import operators as ops
from rx.core.typing import Disposable
from rx.subject import Subject
from typing import List, NamedTuple
from intelino.trainlib_async import (
    TrainScanner,
    Train,
)
from intelino.trainlib_async.messages import (
    TrainMsgEventFrontColorChanged,
    TrainMsgMovement,
)
from intelino.trainlib_async.enums import SnapColorValue as Color, SteeringDecision
from intelino.trainlib_async.helpers import AsyncObserver

#
# Data types
#

SectionState = Enum("SectionState", "FREE OCCUPIED_BY")


class SectionInfo(NamedTuple):
    state: SectionState
    train_id: int


class Message(NamedTuple):
    """The message format to be passed in the shared stream."""

    section_color: Color
    section_info: SectionInfo


class SharedState:
    """Class for a global state shared between all train programs and also
    the shared logic.
    """

    def __init__(self):
        self.exit_event = asyncio.Event()
        # critical section update stream
        self.stream = Subject()  # type: Subject[Message]
        # critical section state (updated by the SharedLogic from the stream)
        self.critical_section = {
            Color.YELLOW: SectionInfo(SectionState.FREE, -1),
            Color.MAGENTA: SectionInfo(SectionState.FREE, -1),
        }

    def dispose(self):
        self.stream.on_completed()
        self.stream.dispose()


class LocalState:
    def __init__(self):
        # waiting on the entry to the critical section
        self.waiting = {
            Color.YELLOW: False,
            Color.MAGENTA: False,
        }


#
# Shared logic
#


class SharedLogic:
    """The programs' own logic can execute actions based on the shared state
    and the shared data stream. It can manipulate the shared state
    but communication with trains is strictly through message passing.
    """

    def __init__(self, shared_state: SharedState):
        self.shared_state = shared_state

    async def run(self):
        # Any "active" logic (e.g. user inputs, signalling to trains etc.)
        # would be run through this function.
        subscription = self.shared_state.stream.subscribe(
            AsyncObserver(self.update_crical_section_state)
        )
        await self.waiter()
        subscription.dispose()

    async def update_crical_section_state(self, m: Message):
        self.shared_state.critical_section[m.section_color] = m.section_info

    async def waiter(self):
        """Let the train program run until the 'enter' key is pressed."""
        await aioconsole.ainput("Press <Enter> to exit at any time...\n")
        self.shared_state.exit_event.set()


#
# Train program (for all trains)
#


async def collision_avoidance(train: Train, index: int, shared_state: SharedState):
    """Two trains prevent head-on collision on two shared sections."""
    state = LocalState()

    async def enter_section(color: Color):
        shared_state.stream.on_next(
            Message(color, SectionInfo(SectionState.OCCUPIED_BY, index))
        )
        state.waiting[color] = False

    async def leave_section(color: Color):
        shared_state.stream.on_next(
            Message(color, SectionInfo(SectionState.FREE, index))
        )

    async def wait_to_enter_section(color: Color):
        state.waiting[color] = True
        await train.stop_driving()

    async def milestone(msg: TrainMsgEventFrontColorChanged):
        if msg.color in shared_state.critical_section:
            # the color identified a critical section entry/exit
            critical_section = shared_state.critical_section[msg.color]
            if critical_section.state == SectionState.FREE:
                # when free, let others know we are entering it
                await enter_section(msg.color)

            elif critical_section == (SectionState.OCCUPIED_BY, index):
                # when it was occupied by us, we are leaving it
                await leave_section(msg.color)

            else:
                # all other cases require us to wait
                await wait_to_enter_section(msg.color)

    async def section_freed(message: Message):
        if state.waiting[message.section_color]:
            await enter_section(message.section_color)
            await train.drive_at_speed(40)

    async def update_steering_decision(msg: TrainMsgMovement):
        # since we have 2 trains and they go in opposite directions,
        # one on the inner loop and one on the outer loop, they use the
        # same decision side on splits
        await train.set_next_split_steering_decision(SteeringDecision.LEFT)

    # create a list of subscriptions
    subscriptions: List[Disposable] = []

    # start the movement stream
    movement_stream = await train.movement_notification_stream(True)
    sub = movement_stream.pipe(
        # we are interested only if the next decision is not set
        ops.filter(lambda msg: msg.next_split_decision == SteeringDecision.NONE),
    ).subscribe(AsyncObserver(update_steering_decision))
    subscriptions.append(sub)

    sub = train.notifications.pipe(
        # we are interested only in color changes
        ops.filter(lambda msg: isinstance(msg, TrainMsgEventFrontColorChanged)),
    ).subscribe(AsyncObserver(milestone))
    subscriptions.append(sub)

    sub = shared_state.stream.pipe(
        ops.filter(lambda msg: msg.section_info.state == SectionState.FREE),
    ).subscribe(AsyncObserver(section_freed))
    subscriptions.append(sub)

    await train.drive_at_speed(35)

    # wait for the exit event to happen
    await shared_state.exit_event.wait()

    # cleanup
    for subscription in subscriptions:
        subscription.dispose()
    await train.stop_driving()


async def main():
    # connect to the first 2 trains discovered
    trains = await TrainScanner().get_trains(count=2)
    shared_state = SharedState()
    shared_logic = SharedLogic(shared_state)

    # run our train program with all our trains
    await asyncio.gather(
        shared_logic.run(),
        *(
            collision_avoidance(train, idx, shared_state)
            for idx, train in enumerate(trains)
        ),
    )

    # after the program finished, clean up and disconnect from the trains
    shared_state.dispose()
    for train in trains:
        await train.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
