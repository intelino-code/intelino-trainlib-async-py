"""Teamwork example: Collision avoidance (v2) with arbitration.

Track requirements (same as v1):
- Double loop (inner + outer) with two "shared" sections
  - outer loop is clockwise (2 trains)
  - inner loop is counter-clockwise (1 train)
- Yellow and magenta snaps are used to identify the shared sections.

Changes:
- arbitration (separating actions and state) solves the issue of multiple
  trains waiting at once and introduces transactional logic
- when the section is freed, the waiting trains re-request entry
  - alternatively (not implemented here), the arbiter (shared logic) could
    implement queueing, so re-requesting entry would not be required
    and whichever train started waiting first, would get the "pass" to enter

Notes (corner cases):
- it still doesn't solve queueing when trains are coming from the same branch,
  tm. it doesn't prevent collisions to the back during congestion on a single
  track.

"""
import asyncio
import aioconsole
from dataclasses import dataclass
from enum import Enum
from rx import operators as ops
from rx.core.typing import Disposable
from rx.subject import Subject
from typing import List, NamedTuple
from intelino.trainlib_async import (
    TrainScanner,
    Train,
    TrainMsgEventFrontColorChanged,
    TrainMsgMovement,
)
from intelino.trainlib_async.enums import SnapColorValue as Color, SteeringDecision
from intelino.trainlib_async.helpers import AsyncObserver

#
# Data types
#

SectionState = Enum("SectionState", "FREE OCCUPIED_BY")
SectionRequest = Enum("SectionState", "ENTER LEAVE")
SectionResponse = Enum("SectionState", "ENTER_APPROVED ENTER_REJECTED SECTION_FREE")

TrainSectionState = Enum("TrainSectionState", "NONE ENTERED WAITING")


class SectionInfo(NamedTuple):
    state: SectionState
    train_id: int


@dataclass(frozen=True)
class Message:
    """The message format to be passed in the shared stream."""

    section_color: Color
    train_id: int


@dataclass(frozen=True)
class MessageRequest(Message):
    request: SectionRequest


@dataclass(frozen=True)
class MessageResponse(Message):
    response: SectionResponse


class SharedState:
    """Class for a global state shared between all train programs and also
    the shared logic.
    """

    def __init__(self):
        self.exit_event = asyncio.Event()
        # critical section request and update stream
        self.stream = Subject()  # type: Subject[Message]
        # critical section state (updated by the SharedLogic from the stream)
        # Note: in this implementation this wouldn't need to be shared
        self.critical_section = {
            Color.YELLOW: SectionInfo(SectionState.FREE, -1),
            Color.MAGENTA: SectionInfo(SectionState.FREE, -1),
        }

    def dispose(self):
        self.stream.on_completed()
        self.stream.dispose()


class LocalState:
    def __init__(self):
        # train-specific critical section state
        self.section: dict[Color, TrainSectionState] = {
            Color.YELLOW: TrainSectionState.NONE,
            Color.MAGENTA: TrainSectionState.NONE,
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
        subscription = self.shared_state.stream.pipe(
            ops.filter(lambda msg: isinstance(msg, MessageRequest))
        ).subscribe(AsyncObserver(self.handle_request))
        await self.waiter()
        subscription.dispose()

    async def handle_request(self, msg: MessageRequest):
        """Arbitration function processing requests as transactions.
        Note: not thread-safe
        """
        section_info = self.shared_state.critical_section[msg.section_color]

        # verify each request, update sections' state and notify all trains
        # through the stream with a response
        if msg.request == SectionRequest.ENTER:
            if section_info.state == SectionState.FREE:
                # allow entry
                self.shared_state.critical_section[msg.section_color] = SectionInfo(
                    SectionState.OCCUPIED_BY, msg.train_id
                )
                self.shared_state.stream.on_next(
                    MessageResponse(
                        msg.section_color, msg.train_id, SectionResponse.ENTER_APPROVED
                    )
                )

            else:
                # reject entry
                self.shared_state.stream.on_next(
                    MessageResponse(
                        msg.section_color, msg.train_id, SectionResponse.ENTER_REJECTED
                    )
                )

        elif msg.request == SectionRequest.LEAVE:
            if section_info == (SectionState.OCCUPIED_BY, msg.train_id):
                # free section
                self.shared_state.critical_section[msg.section_color] = SectionInfo(
                    SectionState.FREE, msg.train_id
                )
                self.shared_state.stream.on_next(
                    MessageResponse(
                        msg.section_color, msg.train_id, SectionResponse.SECTION_FREE
                    )
                )

    async def waiter(self):
        """Let the train program run until the 'enter' key is pressed."""
        await aioconsole.ainput("Press <Enter> to exit at any time...\n")
        self.shared_state.exit_event.set()


#
# Train program (for all trains)
#


async def collision_avoidance(train: Train, index: int, shared_state: SharedState):
    """Multiple trains prevent head-on collision on two shared sections."""
    state = LocalState()

    async def request_entry(color: Color):
        shared_state.stream.on_next(MessageRequest(color, index, SectionRequest.ENTER))

    async def request_leave(color: Color):
        shared_state.stream.on_next(MessageRequest(color, index, SectionRequest.LEAVE))

    async def milestone(msg: TrainMsgEventFrontColorChanged):
        if msg.color in shared_state.critical_section:
            if state.section[msg.color] == TrainSectionState.NONE:
                await request_entry(msg.color)

            elif state.section[msg.color] == TrainSectionState.ENTERED:
                await request_leave(msg.color)

    async def section_enter(color: Color):
        if state.section[color] == TrainSectionState.WAITING:
            await train.drive_at_speed(40)
        state.section[color] = TrainSectionState.ENTERED

    async def section_wait(color: Color):
        if state.section[color] != TrainSectionState.WAITING:
            await train.stop_driving()
        state.section[color] = TrainSectionState.WAITING

    async def section_leave(color: Color):
        state.section[color] = TrainSectionState.NONE

    async def handle_response(msg: MessageResponse):
        if msg.train_id == index:
            # handle all responses addressed to us
            if msg.response == SectionResponse.ENTER_APPROVED:
                await section_enter(msg.section_color)
            elif msg.response == SectionResponse.ENTER_REJECTED:
                await section_wait(msg.section_color)
            elif msg.response == SectionResponse.SECTION_FREE:
                await section_leave(msg.section_color)

        elif msg.response == SectionResponse.SECTION_FREE:
            # listen to all `SECTION_FREE` messages
            if state.section[msg.section_color] == TrainSectionState.WAITING:
                # if we are waiting, we request entry again
                await request_entry(msg.section_color)

    async def update_steering_decision(msg: TrainMsgMovement):
        # since we have 2 loops that are driven in opposite directions,
        # all trains use the same decision side on splits
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
        ops.filter(lambda msg: isinstance(msg, MessageResponse)),
    ).subscribe(AsyncObserver(handle_response))
    subscriptions.append(sub)

    await train.drive_at_speed(35)

    # wait for the exit event to happen
    await shared_state.exit_event.wait()

    # cleanup
    for subscription in subscriptions:
        subscription.dispose()
    await train.stop_driving()


async def main():
    # connect to a few trains
    trains = await TrainScanner(timeout=4.0).get_trains(at_most=3)
    shared_state = SharedState()
    shared_logic = SharedLogic(shared_state)

    if len(trains) >= 2:
        print(f"Connected to {len(trains)} trains.")
        # run our train program with all our trains
        await asyncio.gather(
            shared_logic.run(),
            *(
                collision_avoidance(train, idx, shared_state)
                for idx, train in enumerate(trains)
            ),
        )

    else:
        print("Not enough trains found.")

    # after the program finished, clean up and disconnect from the trains
    shared_state.dispose()
    for train in trains:
        await train.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
