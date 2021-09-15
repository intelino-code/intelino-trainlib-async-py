# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""message.py - Train message definitions (dataclasses)."""

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, ClassVar, Iterable, Tuple, Union

from .enums.enums import (
    ButtonPress,
    ColorSensor,
    MovementDirection,
    SnapColorValue,
    SteeringDecision,
)

if TYPE_CHECKING:
    from .train_ble_packet import TrainBlePacket


class EventId(IntEnum):
    """Event ID."""

    NONE = 0x00
    MOVEMENT_DIRECTION_CHANGED = 0x01
    LOW_BATTERY = 0x02
    BATTERY_CUT_OFF = 0x03
    CHARGING_STATE_CHANGED = 0x04
    BUTTON_PRESS_DETECTED = 0x05
    SNAP_COMMAND_EXECUTED = 0x06
    FRONT_COLOR_CHANGED = 0x07
    BACK_COLOR_CHANGED = 0x08
    SNAP_COMMAND_DETECTED = 0x09
    SPLIT_DECISION = 0x0A


class SnapCommand(
    Tuple[SnapColorValue, SnapColorValue, SnapColorValue, SnapColorValue]
):
    """Snap command is a tuple of 4 colors (:class:`SnapColorValue`).

    It always starts with white or cyan.
    If the snap sequence is shorter, it is padded with black.
    Since white and cyan always start a new snap command, these colors
    will never appear on other position.
    """

    def __str__(self) -> str:
        return str(tuple(str(c) for c in self))

    def __eq__(self, o: object) -> bool:
        """Compare (exact match) the snap command to a tuple of colors.

        Since snap commands are always 4 colors, this allows to exact match
        with shorter tuples.

        Example:
            Note: :class:`SnapColorValue` is imported as ``C`` in this example.

            >>> msg.colors == (C.WHITE, C.RED, C.BLACK, C.BLACK)
            >>> # exact match with implicit blacks
            >>> msg.colors == (C.WHITE, C.RED)
        """
        if isinstance(o, Tuple):
            other = o
        elif isinstance(o, Iterable):
            other = tuple(o)
        else:
            other = o

        if isinstance(other, Tuple):
            no_snaps_fill = (SnapColorValue.BLACK,) * 3
            other = (other + no_snaps_fill)[:4]

        return super().__eq__(other)

    def starts_with(
        self,
        colors: Union[Tuple[SnapColorValue, ...], SnapColorValue],
        *args: SnapColorValue,
    ):
        """Partial / prefix match.

        This function is aliased as :func:`start_with` and :func:`starts_with`
        to be used depending on the context.

        Example:
            Note: :class:`SnapColorValue` is imported as ``C`` in this example.

            >>> snap_command.starts_with(C.WHITE, C.RED)
            >>> msg.colors.start_with(C.CYAN, C.BLUE)

        Args:
            colors (SnapColorValue): It accepts either tuples or multiple
                parameters of :class:`SnapColorValue`.
        """
        if isinstance(colors, Tuple):
            compare_with = colors
        else:
            compare_with = tuple((colors, *args))

        for idx, color in enumerate(compare_with):
            if (idx >= len(self)) or (self[idx] != color):
                return False

        return True

    # alias
    start_with = starts_with


@dataclass(frozen=True)
class TrainMsgBase:
    """Base train message."""

    command_id: ClassVar[int]
    raw_packet: "TrainBlePacket"


@dataclass(frozen=True)
class TrainMsgEventBase(TrainMsgBase):
    """Base event message."""

    command_id: ClassVar[int] = 0xE0
    event_id: ClassVar[EventId]
    # Timestamp of the moment when the event happened in "train" time
    timestamp_ms: int


@dataclass(frozen=True)
class TrainMsgUnknown(TrainMsgBase):
    command_id: ClassVar[int] = 0x00


@dataclass(frozen=True)
class TrainMsgEventUnknown(TrainMsgEventBase):
    command_id: ClassVar[int] = 0x00
    event_id: ClassVar[EventId] = EventId.NONE


@dataclass(frozen=True)
class TrainMsgMalformed(TrainMsgBase):
    command_id: ClassVar[int] = 0x0100


@dataclass(frozen=True)
class TrainMsgMacAddress(TrainMsgBase):
    command_id: ClassVar[int] = 0x42
    mac_address: str


@dataclass(frozen=True)
class TrainMsgTrainUuid(TrainMsgBase):
    command_id: ClassVar[int] = 0x43
    uuid: str


@dataclass(frozen=True)
class TrainMsgVersionDetail(TrainMsgBase):
    """Train version information."""

    @dataclass(frozen=True)
    class Version:
        """Version number tuple."""

        def __str__(self) -> str:
            return (
                f"{self.major}.{self.minor}.{self.patch}"
                if self.patch is not None
                else f"{self.major}.{self.minor}"
            )

        major: int
        minor: int
        patch: Union[int, None] = None

    command_id: ClassVar[int] = 0x07
    ble_api_version: Version
    fw_version: Version


@dataclass(frozen=True)
class TrainMsgStatsLifetimeOdometer(TrainMsgBase):
    command_id: ClassVar[int] = 0x3E
    # Absolute (lifetime) odometer value in meters. The precision is in cm.
    # Preserved after the train is turned off.
    lifetime_odometer_meters: float


@dataclass(frozen=True)
class TrainMsgMovement(TrainMsgBase):
    """Movement stream message."""

    command_id: ClassVar[int] = 0xB7
    # Movement direction forward, backward, or stop.
    direction: MovementDirection
    # Current speed in cm/s.
    speed_cmps: float
    # Current PWM value on motor. Range: 0 (stopped) to 255 (full duty).
    pwm: int
    # Speed control (PID) status.
    speed_control: bool
    # The target speed for speed control (if turned on).
    desired_speed_cmps: float
    # Pause time in ms. 0 means no pause.
    pause_time_ms: int
    # Next split decision. It can be left, right, straight, or `NONE`, which
    # means it is random or based on the directional snap on the split track.
    next_split_decision: SteeringDecision
    # Absolute (lifetime) odometer value in meters. The precision is in cm.
    # Preserved after the train is turned off.
    lifetime_odometer_meters: float


@dataclass(frozen=True)
class TrainMsgEventMovementDirectionChanged(TrainMsgEventBase):
    """Triggered whenever the direction changes or the train stops."""

    event_id: ClassVar[EventId] = EventId.MOVEMENT_DIRECTION_CHANGED
    direction: MovementDirection


@dataclass(frozen=True)
class TrainMsgEventLowBattery(TrainMsgEventBase):
    """Triggered when the battery voltage is low."""

    event_id: ClassVar[EventId] = EventId.LOW_BATTERY


@dataclass(frozen=True)
class TrainMsgEventLowBatteryCutOff(TrainMsgEventBase):
    """Triggered when the train turns off due to low battery."""

    event_id: ClassVar[EventId] = EventId.BATTERY_CUT_OFF


@dataclass(frozen=True)
class TrainMsgEventChargingStateChanged(TrainMsgEventBase):
    """Triggered when the charger is connected or disconnected."""

    event_id: ClassVar[EventId] = EventId.CHARGING_STATE_CHANGED
    is_charging: bool


@dataclass(frozen=True)
class TrainMsgEventButtonPressDetected(TrainMsgEventBase):
    """Triggered when the train’s button is pressed. The detection does not
    affect the button’s functionality (start/stop driving on a short press,
    turn off on a long press).
    """

    event_id: ClassVar[EventId] = EventId.BUTTON_PRESS_DETECTED
    button_press_type: ButtonPress


@dataclass(frozen=True)
class TrainMsgEventSnapCommandDetected(TrainMsgEventBase):
    """Triggered when a snap sequence (command) is detected, regardless of the execution status."""

    event_id: ClassVar[EventId] = EventId.SNAP_COMMAND_DETECTED
    # Verification snap counter. Overflows after 255.
    snap_counter: int
    # Tuple of 4 colors.
    colors: SnapCommand


@dataclass(frozen=True)
class TrainMsgEventSnapCommandExecuted(TrainMsgEventBase):
    """Triggered after the snap sequence (command) execution started.

    If snap execution is turned off, this event will not be sent.
    """

    event_id: ClassVar[EventId] = EventId.SNAP_COMMAND_EXECUTED
    # Verification snap counter. Overflows after 255.
    snap_counter: int
    # Tuple of 4 colors.
    colors: SnapCommand


@dataclass(frozen=True)
class TrainMsgEventSensorColorChangedBase(TrainMsgEventBase):
    """Triggered after the color is accepted by the train."""

    sensor: ClassVar[ColorSensor]
    color: SnapColorValue


@dataclass(frozen=True)
class TrainMsgEventFrontColorChanged(TrainMsgEventSensorColorChangedBase):
    """Train's front color sensor."""

    event_id: ClassVar[EventId] = EventId.FRONT_COLOR_CHANGED
    sensor: ClassVar[ColorSensor] = ColorSensor.FRONT


@dataclass(frozen=True)
class TrainMsgEventBackColorChanged(TrainMsgEventSensorColorChangedBase):
    """Train's back color sensor."""

    event_id: ClassVar[EventId] = EventId.BACK_COLOR_CHANGED
    sensor: ClassVar[ColorSensor] = ColorSensor.BACK


@dataclass(frozen=True)
class TrainMsgEventSplitDecision(TrainMsgEventBase):
    """Triggered after the split track is detected and the steering decision is made."""

    event_id: ClassVar[EventId] = EventId.SPLIT_DECISION
    decision: SteeringDecision


"""Useful for shared color change handler to process both color sensors with
one function."""
TrainMsgEventSensorColorChanged = Union[
    TrainMsgEventFrontColorChanged,
    TrainMsgEventBackColorChanged,
]

TrainMsgEvent = Union[
    TrainMsgEventUnknown,
    TrainMsgEventMovementDirectionChanged,
    TrainMsgEventLowBattery,
    TrainMsgEventLowBatteryCutOff,
    TrainMsgEventChargingStateChanged,
    TrainMsgEventButtonPressDetected,
    TrainMsgEventSnapCommandExecuted,
    TrainMsgEventSensorColorChanged,
    TrainMsgEventSnapCommandDetected,
    TrainMsgEventSplitDecision,
]

TrainMsg = Union[
    TrainMsgUnknown,
    TrainMsgMalformed,
    TrainMsgMacAddress,
    TrainMsgTrainUuid,
    TrainMsgVersionDetail,
    TrainMsgStatsLifetimeOdometer,
    TrainMsgMovement,
    TrainMsgEvent,
]
