"""Teamwork example: Merge protection to avoid collisions (for two trains).

Track requirements:
- track with a split track (e.g. small and big loop), both trains driving
  in the same direction
- snaps:
  - white-magenta: identifies the entry to the critical section

Notes (corner cases):
- Since both entries are identified the same way, the second train will always
  need to wait until the first one leaves the critical section, even if they
  are both coming from the same side.
- When the critical section is freed, all waiting trains are released. That
  means this example code works only when there is exactly one train waiting.

"""
import asyncio
import aioconsole
from enum import Enum
from rx import operators as ops
from rx.core.typing import Disposable
from rx.subject import BehaviorSubject
from typing import List, NamedTuple
from intelino.trainlib_async import (
    TrainScanner,
    Train,
)
from intelino.trainlib_async.messages import (
    TrainMsgEventSnapCommandDetected,
)
from intelino.trainlib_async.enums import SnapColorValue as Color
from intelino.trainlib_async.helpers import AsyncObserver

#
# Data types
#

SectionState = Enum("SectionState", "FREE OCCUPIED_BY")


class SectionInfo(NamedTuple):
    state: SectionState
    train_id: int


class SharedState:
    def __init__(self):
        self.exit_event = asyncio.Event()
        # critical section info stream
        self.critical_section = BehaviorSubject(SectionInfo(SectionState.FREE, -1))

    def dispose(self):
        self.critical_section.on_completed()
        self.critical_section.dispose()


class LocalState:
    def __init__(self):
        # waiting on the entry to the critical section
        self.waiting = False


#
# Functions
#


async def waiter(event: asyncio.Event):
    """Let the train program run until the 'enter' key is pressed."""
    await aioconsole.ainput("Press <Enter> to exit at any time...\n")
    event.set()


async def merge_protection(train: Train, index: int, shared_state: SharedState):
    """Two trains prevent collisions on a single merge."""
    state = LocalState()

    async def milestone(msg: TrainMsgEventSnapCommandDetected):
        if msg.colors == (Color.WHITE, Color.MAGENTA, Color.BLACK, Color.BLACK):
            # critical section entry
            if shared_state.critical_section.value.state == SectionState.FREE:
                # when free, let others know we are entering it
                shared_state.critical_section.on_next(
                    SectionInfo(SectionState.OCCUPIED_BY, index)
                )

            else:
                # when not free, wait until it is freed
                state.waiting = True
                await train.stop_driving()

        elif msg.colors == (Color.CYAN, Color.BLACK, Color.BLACK, Color.BLACK):
            # since we are protecting a single merge track, we can use
            # its built-in snaps to detect when are we leaving the critical
            # section
            if shared_state.critical_section.value == (SectionState.OCCUPIED_BY, index):
                # only if it was occupied by us, free it
                shared_state.critical_section.on_next(
                    SectionInfo(SectionState.FREE, index)
                )

    async def section_freed(info: SectionInfo):
        if state.waiting:
            shared_state.critical_section.on_next(
                SectionInfo(SectionState.OCCUPIED_BY, index)
            )
            await train.drive_at_speed(40)
            state.waiting = False

    # create a list of subscriptions
    subscriptions: List[Disposable] = []

    sub = train.notifications.pipe(
        # we are interested only in snap events, so we filter the stream
        ops.filter(lambda msg: isinstance(msg, TrainMsgEventSnapCommandDetected)),
    ).subscribe(AsyncObserver(milestone))
    subscriptions.append(sub)

    sub = shared_state.critical_section.pipe(
        ops.filter(lambda section: section.state == SectionState.FREE),
    ).subscribe(AsyncObserver(section_freed))
    subscriptions.append(sub)

    # clear all custom snap commands stored on the train (just to be sure)
    await train.clear_custom_snap_commands()

    await train.drive_at_speed(40)

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

    # run our train program with all our trains
    await asyncio.gather(
        waiter(shared_state.exit_event),
        *(
            merge_protection(train, idx, shared_state)
            for idx, train in enumerate(trains)
        ),
    )

    # after the program finished, clean up and disconnect from the trains
    shared_state.dispose()
    for train in trains:
        await train.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
