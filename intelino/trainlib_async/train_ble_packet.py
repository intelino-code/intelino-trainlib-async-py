# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""train_ble_packet.py"""

from typing import Iterable, Optional, Type, TypeVar, Union

from .exc import TrainMessageTypeError, TrainlibError
from .messages import TrainMsg, TrainMsgBase
from .message_builder import MessageBuilder


T = TypeVar("T", bound="TrainMsgBase")


class TrainBlePacket:
    """Train BLE Packet class (over a bytearray)."""

    def __init__(self, data: Union[bytearray, Iterable[int]]) -> None:
        self.data: bytearray
        if isinstance(data, bytearray):
            self.data = data
        else:
            self.data = bytearray(int(val) & 0xFF for val in data)

    def __str__(self) -> str:
        return ":".join([f"{byte:02x}" for byte in self.data])

    def __repr__(self) -> str:
        return "<{0}, {1}>".format(
            self.__class__.__name__,
            str(self),
        )

    @property
    def command(self) -> int:
        return self.data[0] if self.data else 0

    @property
    def payload(self) -> bytearray:
        return self.data[2:] if self.data else bytearray()

    @property
    def msg(self) -> TrainMsg:
        try:
            return MessageBuilder.create(self)
        except TrainlibError:
            return MessageBuilder.create_malformed(self)

    def get_interpreted_message(self, msg_type: Type[T]) -> T:
        msg = MessageBuilder.create(self)

        if isinstance(msg, msg_type):
            return msg

        raise TrainMessageTypeError(
            f"Wrong message type {msg_type} expected! The type was {type(msg)}"
        )

    def make_hex_string(
        self, with_header: bool = True, delimiter: str = ":", with_garbage: bool = False
    ) -> str:
        data = self.data if (with_header) else self.data[2:]
        if not with_garbage:
            length = self.data[1] if (len(self.data) >= 2) else 0
            data = data[:length]

        return delimiter.join([f"{byte:02x}" for byte in data])

    @classmethod
    def from_command(
        cls,
        command_id: int,
        payload: Iterable[int] = None,
        length: Optional[int] = None,
    ) -> "TrainBlePacket":
        """Factory method with optional args."""
        payload_data = payload or []
        return cls(
            [
                command_id,
                len(list(payload_data)) if length is None else length,
                *payload_data,
            ]
        )

    @classmethod
    def from_hex_string(cls, data_string: str) -> "TrainBlePacket":
        """Factory method from strings like 06:02:BA:BE."""
        return cls(list(map(lambda v: int(v, 16), data_string.split(":"))))
