# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""message_builder.py - Parse `TrainBlePacket` into some `TrainMsg*`."""

import struct
from typing import NamedTuple, TYPE_CHECKING

from .exc import TrainMessageLengthError
from .enums.enums import (
    ButtonPress,
    MovementDirection,
    SteeringDecision,
    _OldSteeringDecision,
    SnapColorValue,
    _convert_from_old_steering_decision,
)
from .messages import (
    SnapCommand,
    TrainMsgEvent,
    TrainMsgEventBackColorChanged,
    TrainMsgEventBase,
    TrainMsgEventButtonPressDetected,
    TrainMsgEventChargingStateChanged,
    TrainMsgEventFrontColorChanged,
    TrainMsgEventLowBattery,
    TrainMsgEventLowBatteryCutOff,
    TrainMsgEventMovementDirectionChanged,
    TrainMsgEventSnapCommandDetected,
    TrainMsgEventSnapCommandExecuted,
    TrainMsgEventSplitDecision,
    TrainMsgEventUnknown,
    TrainMsgMacAddress,
    TrainMsgMalformed,
    TrainMsgMovement,
    TrainMsg,
    TrainMsgStatsLifetimeOdometer,
    TrainMsgTrainUuid,
    TrainMsgUnknown,
    TrainMsgVersionDetail,
)

if TYPE_CHECKING:
    from .train_ble_packet import TrainBlePacket


class MessageBuilder:
    """Build response messages from raw packets received from the train."""

    # offset of event id and timestamp
    EVENT_PAYLOAD_OFFSET = 5

    class EventCommonData(NamedTuple):
        id: int
        timestamp_ms: int

    @classmethod
    def create_unknown(cls, packet: "TrainBlePacket"):
        """This function can be used as a fallback when message creation fails."""
        return TrainMsgUnknown(raw_packet=packet)

    @classmethod
    def create_malformed(cls, packet: "TrainBlePacket"):
        """This function can be used as a fallback when message creation fails."""
        return TrainMsgMalformed(raw_packet=packet)

    @classmethod
    def create(cls, packet: "TrainBlePacket") -> TrainMsg:

        if packet.command == TrainMsgEventBase.command_id:
            return cls._create_event(packet)

        elif packet.command == TrainMsgMacAddress.command_id:
            return cls._mac_address(packet)

        elif packet.command == TrainMsgTrainUuid.command_id:
            return cls._train_uuid(packet)

        elif packet.command == TrainMsgVersionDetail.command_id:
            return cls._version_info(packet)

        elif packet.command == TrainMsgStatsLifetimeOdometer.command_id:
            return cls._stats_lifetime_odometer(packet)

        elif packet.command == TrainMsgMovement.command_id:
            return cls._movement(packet)

        return cls.create_unknown(packet)

    @classmethod
    def _create_event(cls, packet: "TrainBlePacket") -> TrainMsgEvent:
        unpacked_data = cls._unpack(">BL", packet)
        event = cls.EventCommonData(
            id=unpacked_data[0],
            timestamp_ms=unpacked_data[1],
        )

        if event.id == TrainMsgEventMovementDirectionChanged.event_id:
            return cls._event_movement_direction_changed(event, packet)

        elif event.id == TrainMsgEventLowBattery.event_id:
            return TrainMsgEventLowBattery(
                raw_packet=packet,
                timestamp_ms=event.timestamp_ms,
            )

        elif event.id == TrainMsgEventLowBatteryCutOff.event_id:
            return TrainMsgEventLowBatteryCutOff(
                raw_packet=packet,
                timestamp_ms=event.timestamp_ms,
            )

        elif event.id == TrainMsgEventChargingStateChanged.event_id:
            return cls._event_charging_state_changed(event, packet)

        elif event.id == TrainMsgEventButtonPressDetected.event_id:
            return cls._event_button_press_detected(event, packet)

        elif event.id == TrainMsgEventSnapCommandExecuted.event_id:
            return cls._event_snap_executed(event, packet)

        elif event.id == TrainMsgEventFrontColorChanged.event_id:
            return cls._event_front_color_changed(event, packet)

        elif event.id == TrainMsgEventBackColorChanged.event_id:
            return cls._event_back_color_changed(event, packet)

        elif event.id == TrainMsgEventSnapCommandDetected.event_id:
            return cls._event_snap_detected(event, packet)

        elif event.id == TrainMsgEventSplitDecision.event_id:
            return cls._event_split_decision(event, packet)

        return TrainMsgEventUnknown(
            raw_packet=packet,
            timestamp_ms=event.timestamp_ms,
        )

    @classmethod
    def _unpack(cls, data_format: str, packet: "TrainBlePacket", offset: int = 0):
        required_length = struct.calcsize(data_format) + offset
        if len(packet.payload) < required_length:
            raise TrainMessageLengthError(
                f"Packet {packet} payload too short! Expected at least {required_length} bytes."
            )

        try:
            return struct.unpack(data_format, packet.payload[offset:required_length])
        except struct.error as exc:
            raise TrainMessageLengthError(
                f"Packet {packet} payload couldn't be parsed as '{data_format}'."
            ) from exc

    @classmethod
    def _mac_address(cls, packet: "TrainBlePacket"):
        if len(packet.payload) < 6:
            raise TrainMessageLengthError(
                f"Packet {packet} payload too short! Expected at least {6} bytes."
            )

        return TrainMsgMacAddress(
            raw_packet=packet, mac_address=packet.make_hex_string(with_header=False)
        )

    @classmethod
    def _train_uuid(cls, packet: "TrainBlePacket"):
        if len(packet.payload) < 8:
            raise TrainMessageLengthError(
                f"Packet {packet} payload too short! Expected at least {8} bytes."
            )

        # delimited pairs
        # hexstr = [f"{byte:02x}" for byte in packet.data[2:]]
        # pairs = ["".join(bytes) for bytes in zip(hexstr[0::2], hexstr[1::2])]
        # uuid = ":".join(pairs)

        return TrainMsgTrainUuid(
            raw_packet=packet,
            uuid=packet.make_hex_string(with_header=False),
        )

    @classmethod
    def _version_info(cls, packet: "TrainBlePacket"):
        unpacked_data = cls._unpack(">BBBBBBBBB", packet)
        return TrainMsgVersionDetail(
            raw_packet=packet,
            ble_api_version=TrainMsgVersionDetail.Version(
                unpacked_data[4], unpacked_data[5]
            ),
            fw_version=TrainMsgVersionDetail.Version(
                unpacked_data[6], unpacked_data[7], unpacked_data[8]
            ),
        )

    @classmethod
    def _stats_lifetime_odometer(cls, packet: "TrainBlePacket"):
        (lifetime_odometer_cm,) = cls._unpack(">L", packet)
        if lifetime_odometer_cm == 0xFFFFFFFF:
            lifetime_odometer_cm = 0

        return TrainMsgStatsLifetimeOdometer(
            raw_packet=packet,
            lifetime_odometer_meters=lifetime_odometer_cm / 100.0,
        )

    @classmethod
    def _movement(cls, packet: "TrainBlePacket"):
        data = cls._unpack(">BHB?HBB?BBLBB", packet)
        direction = data[0]
        speed_mmps = data[1]
        pwm = data[2]
        speed_control = data[3]
        desired_speed_mmps = data[4]
        pause_time = data[5]
        next_decision = data[6]
        lifetime_odometer_cm = data[10]

        if lifetime_odometer_cm == 0xFFFFFFFF:
            lifetime_odometer_cm = 0

        return TrainMsgMovement(
            raw_packet=packet,
            direction=MovementDirection(direction),
            speed_cmps=speed_mmps / 10,
            pwm=0xFF - pwm,
            speed_control=speed_control,
            desired_speed_cmps=desired_speed_mmps / 10,
            pause_time_ms=pause_time * 10,
            next_split_decision=_convert_from_old_steering_decision(
                _OldSteeringDecision(next_decision)
            ),
            lifetime_odometer_meters=lifetime_odometer_cm / 100.0,
        )

    @classmethod
    def _event_movement_direction_changed(
        cls, event: EventCommonData, packet: "TrainBlePacket"
    ):
        (direction,) = cls._unpack(">B", packet, cls.EVENT_PAYLOAD_OFFSET)

        return TrainMsgEventMovementDirectionChanged(
            raw_packet=packet,
            timestamp_ms=event.timestamp_ms,
            direction=MovementDirection(direction),
        )

    @classmethod
    def _event_charging_state_changed(
        cls, event: EventCommonData, packet: "TrainBlePacket"
    ):
        (charging,) = cls._unpack(">?", packet, cls.EVENT_PAYLOAD_OFFSET)

        return TrainMsgEventChargingStateChanged(
            raw_packet=packet,
            timestamp_ms=event.timestamp_ms,
            is_charging=charging,
        )

    @classmethod
    def _event_button_press_detected(
        cls, event: EventCommonData, packet: "TrainBlePacket"
    ):
        (press_type,) = cls._unpack(">B", packet, cls.EVENT_PAYLOAD_OFFSET)

        return TrainMsgEventButtonPressDetected(
            raw_packet=packet,
            timestamp_ms=event.timestamp_ms,
            button_press_type=ButtonPress(press_type),
        )

    @classmethod
    def _event_snap_executed(cls, event: EventCommonData, packet: "TrainBlePacket"):
        counter, c1, c2, c3, c4 = cls._unpack(
            ">BBBBB", packet, cls.EVENT_PAYLOAD_OFFSET
        )

        return TrainMsgEventSnapCommandExecuted(
            raw_packet=packet,
            timestamp_ms=event.timestamp_ms,
            snap_counter=counter,
            colors=SnapCommand(SnapColorValue(c) for c in (c1, c2, c3, c4)),
        )

    @classmethod
    def _event_snap_detected(cls, event: EventCommonData, packet: "TrainBlePacket"):
        counter, c1, c2, c3, c4 = cls._unpack(
            ">BBBBB", packet, cls.EVENT_PAYLOAD_OFFSET
        )

        return TrainMsgEventSnapCommandDetected(
            raw_packet=packet,
            timestamp_ms=event.timestamp_ms,
            snap_counter=counter,
            colors=SnapCommand(map(SnapColorValue, (c1, c2, c3, c4))),
        )

    @classmethod
    def _event_front_color_changed(
        cls, event: EventCommonData, packet: "TrainBlePacket"
    ):
        data = cls._unpack(">LB", packet, cls.EVENT_PAYLOAD_OFFSET)

        return TrainMsgEventFrontColorChanged(
            raw_packet=packet,
            timestamp_ms=event.timestamp_ms,
            color=SnapColorValue(data[1]),
        )

    @classmethod
    def _event_back_color_changed(
        cls, event: EventCommonData, packet: "TrainBlePacket"
    ):
        data = cls._unpack(">LB", packet, cls.EVENT_PAYLOAD_OFFSET)

        return TrainMsgEventBackColorChanged(
            raw_packet=packet,
            timestamp_ms=event.timestamp_ms,
            color=SnapColorValue(data[1]),
        )

    @classmethod
    def _event_split_decision(cls, event: EventCommonData, packet: "TrainBlePacket"):
        data = cls._unpack(">BL", packet, cls.EVENT_PAYLOAD_OFFSET)

        return TrainMsgEventSplitDecision(
            raw_packet=packet,
            timestamp_ms=event.timestamp_ms,
            decision=SteeringDecision(data[0]),
        )
