# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""train.py - Train class with async API."""

import asyncio
from typing import Iterable, Union
from rx.core.observable.observable import Observable
from rx import operators as ops

from .messages import (
    TrainMsgMacAddress,
    TrainMsgMovement,
    TrainMsgStatsLifetimeOdometer,
    TrainMsgTrainUuid,
    TrainMsgVersionDetail,
)
from .enums.enums import (
    MovementDirection,
    SteeringDecision,
    SnapColorValue,
    SpeedLevel,
    StopDrivingFeedbackType,
    _convert_to_old_steering_decision,
)
from .enums.internals import BehaviorFeedback, RGBLedGroupId, StreamingRequestFlags
from .train_ble_device import TrainBleDevice
from .train_ble_packet import TrainBlePacket


class Train:
    """Train class with async API."""

    def __init__(self, device: TrainBleDevice):
        self._device: TrainBleDevice = device
        self.__alias = ""

    @property
    def id(self) -> str:
        """Connection ID / address."""
        return self._device.id

    @property
    def name(self) -> str:
        """Advertised name."""
        return self._device.name

    @property
    def alias(self) -> str:
        """User-defined nickname (train alias)."""
        return self.__alias

    @alias.setter
    def alias(self, value: str) -> None:
        self.__alias = value

    @property
    def connection_status(self) -> Observable:
        return self._device.connection_status

    @property
    def is_connected(self) -> bool:
        return self._device.is_connected

    @property
    def notifications(self) -> Observable:  # Observable[TrainMsg]:
        """Response and event stream from the train.

        This observable stream emits all messages coming from the train as
        :class:`TrainMsg`. It can be filtered based on the type of the message.
        """
        return self._device.notifications.pipe(ops.map(lambda packet: packet.msg))

    @property
    def writes(self) -> Observable:
        return self._device.writes

    async def connect(self, force: bool = False, **kwargs):
        """Connect to the train."""
        return await self._device.connect(force, **kwargs)

    async def disconnect(self):
        """Disconnect from the train."""
        # Note: Wait 100 ms before disconnecting just to make sure all
        #   seemingly finished commands are really received by the train.
        await asyncio.sleep(0.100)
        return await self._device.disconnect()

    async def send_command(self, command_id: int, payload: Iterable[int] = None):
        payload_data = payload or []
        return await self._device.send_command(
            TrainBlePacket.from_command(command_id, payload_data)
        )

    async def send_command_with_response(
        self, command_id: int, payload: Iterable[int] = None, timeout: float = 3.0
    ) -> "TrainBlePacket":
        payload_data = payload or []
        return await self._device.send_command_with_response(
            TrainBlePacket.from_command(command_id, payload_data), timeout
        )

    async def get_mac_address(self):
        res = await self.send_command_with_response(0x42)
        return res.get_interpreted_message(TrainMsgMacAddress)

    async def get_uuid(self):
        res = await self.send_command_with_response(0x43)
        return res.get_interpreted_message(TrainMsgTrainUuid)

    async def get_version_info(self):
        res = await self.send_command_with_response(0x07)
        return res.get_interpreted_message(TrainMsgVersionDetail)

    async def get_stats_lifetime_odometer(self):
        """Get lifetime odometer value in meters (precision in cm)."""
        res = await self.send_command_with_response(0x3E)
        return res.get_interpreted_message(TrainMsgStatsLifetimeOdometer)

    async def drive_at_speed(
        self,
        speed_cmps: Union[int, float],
        direction: MovementDirection = MovementDirection.FORWARD,
        play_feedback: bool = True,
    ):
        """Drive with speed control at the given speed in cm/s.

        Args:
            speed_cmps: Desired speed in cm/s. Possible (drivable) values are 15-75 cm/s,
                but not all values are possible (only multiples of 0.9425 cm).
            direction: Movement direction forward (1), backward (2), stop (3) etc.
            play_feedback: Sound and lights.
        """
        return await self.send_command(
            0xBA, [direction, int(speed_cmps), play_feedback]
        )

    async def drive_at_speed_level(
        self,
        speed_level: SpeedLevel,
        direction: MovementDirection = MovementDirection.FORWARD,
        play_feedback: bool = True,
    ):
        """Start driving at a speed level defined by the train (and green snaps).

        Args:
            speed_level: 1, 2, 3.
            direction: Movement direction forward (1), backward (2), stop (3) etc.
            play_feedback: Sound and lights.
        """
        return await self.send_command(0xB8, [direction, speed_level, play_feedback])

    async def drive_with_constant_pwm(
        self,
        pwm: int,
        direction: MovementDirection = MovementDirection.FORWARD,
        play_feedback: bool = True,
    ):
        """Drive without speed control directly setting the motor's PWM level.

        Args:
            pwm: Motor's PWM value from 0 (stopped) to 255 (full power).
            direction: Movement direction forward (1), backward (2), stop (3) etc.
            play_feedback: Sound and lights.
        """
        return await self.send_command(
            0xBC, [direction, 0xFF - (pwm & 0xFF), play_feedback]
        )

    async def stop_driving(
        self,
        play_feedback_type: StopDrivingFeedbackType = StopDrivingFeedbackType.MOVEMENT_STOP,
    ):
        """Stop the train.

        Args:
            play_feedback: Sound and lights.
        """
        # for BLE >= v1.2
        return await self.send_command(0xB9, [play_feedback_type])

    async def pause_driving(self, time: float, play_feedback: bool = True):
        """Stop (pause) movement for the given time and restore it after the time passes.

        Args:
            time (float): Time in seconds (max 25.5).
            play_feedback (bool): Sound and lights.
        """
        return await self.send_command(0xBE, [int(time * 10), play_feedback])

    async def set_next_split_steering_decision(self, next_decision: SteeringDecision):
        """This steering decision is valid for the next split (detected by it’s snaps).
            It overrides the snap value (if set) or the random choice.

        Args:
            next: The next decision.
        """
        return await self.send_command(
            0xBF, [_convert_to_old_steering_decision(next_decision)]
        )

    async def set_top_led_color(self, r: int, g: int, b: int):
        """Set the top RGB LED color.

        Args:
            r (int): 8bit RGB value for red.
            g (int): 8bit RGB value for green.
            b (int): 8bit RGB value for blue.
        """
        return await self.send_command(0xB1, [RGBLedGroupId.TOP, r, g, b])

    async def set_headlight_color(
        self, front: Iterable[int] = None, back: Iterable[int] = None
    ):
        """Set front and back headlight color (for driving). They switch based
            on movement direction. To reset colors call without parameters.

        Args:
            front: Front 8bit RGB value array [red, green, blue].
            back: Back 8bit RGB value array [red, green, blue].
        """
        led_group_mask = 0b000

        if front is not None:
            led_group_mask |= 0b010
            if len(list(front)) != 3:
                front = [*front, 0, 0, 0][:3]
        else:
            front = [0, 0, 0]

        if back is not None:
            led_group_mask |= 0b100
            if len(list(back)) != 3:
                back = [*back, 0, 0, 0][:3]
        else:
            back = [0, 0, 0]

        return await self.send_command(0xB4, [led_group_mask, *front, *back])

    async def get_movement_notification(self) -> TrainMsgMovement:
        """Get a single movement notification."""
        response = await self.send_command_with_response(
            0xB7, [StreamingRequestFlags.GET_ONCE]
        )
        return response.get_interpreted_message(TrainMsgMovement)

    async def movement_notification_stream(
        self, streaming: bool = True, interval: float = 0.1
    ) -> Observable:  # Observable[TrainMsgMovement]:
        """Start or stop movement notification stream.

        Args:
            streaming (bool): True/False to start/stop stream. Null to leave it
                as is (e.g. when only getting once).
            interval (float): Delay between streamed notifications in seconds.
                Minimal value is 0.1s (100ms) and maximal value
                is 2.550s (2550ms). Precision is 0.010s (10ms).
        """
        payload = [
            StreamingRequestFlags.STREAMING_START
            if streaming
            else StreamingRequestFlags.STREAMING_STOP,
            min(max(10, int(interval * 100)), 255),
        ]
        await self.send_command(0xB7, payload)

        return self.notifications.pipe(
            # pass only movement notifications
            ops.filter(lambda p: isinstance(p, TrainMsgMovement)),
        )

    async def set_snap_command_feedback(self, sound: bool, lights: bool):
        """Set snap behavior feedback (from BLE API v1.2).

        Args:
            sound (bool): Sounds on/off.
            lights (bool): Blink top LED on/off.
        """
        bit_mask = BehaviorFeedback.EMPTY

        if sound:
            bit_mask |= BehaviorFeedback.SOUND

        if lights:
            bit_mask |= BehaviorFeedback.LIGHTS

        return await self.send_command(0x65, [bit_mask])

    async def set_snap_command_execution(self, on: bool):
        """Enable or disable snap command execution on the train (from BLE API v1.2).

        Args:
            on (bool): Snap execution on/off.
        """
        return await self.send_command(0x41, [on])

    async def clear_custom_snap_commands(self):
        """Clear user defined custom snap commands stored in the train to avoid
        collisions in behavior in case we would listen and react to these
        events.
        """
        await self.send_command(0x64, [SnapColorValue.BLACK, 0x00])
        await self.send_command(0x64, [SnapColorValue.RED, 0x00])
        await self.send_command(0x64, [SnapColorValue.GREEN, 0x00])
        await self.send_command(0x64, [SnapColorValue.YELLOW, 0x00])
        await self.send_command(0x64, [SnapColorValue.BLUE, 0x00])

    async def decouple_wagon(self, play_feedback: bool = True):
        """Decouple wagon.

        Args:
            play_feedback: Sound and lights.
        """
        # magnet for 512 ms = 0x0200
        await self.send_command(0x80, [0x02, 0x00, play_feedback])
