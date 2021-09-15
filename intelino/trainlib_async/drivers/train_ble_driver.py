# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""train_ble_driver.py"""

import abc
from typing import Callable

from ..train_ble_packet import TrainBlePacket


class TrainBleDriver(abc.ABC):
    """Abstract Train BLE Driver parent class."""

    COMMAND_SERVICE = "43dfd9e9-17e5-4860-803d-9df8999b0d7a"
    COMMAND_CHARACTERISTIC = "40c540d0-344c-4d0d-a1da-9cc260b82d43"
    RESPONSE_SERVICE = "4dad4922-5c86-4ba7-a2e1-0f240537bd08"
    RESPONSE_CHARACTERISTIC = "a4b80869-a84c-4160-a3e0-72fa58ff480e"

    def __str__(self):
        return "{0}: {1} ({2})".format(self.__class__.__name__, self.name, self.id)

    def __repr__(self):
        return "<{0}, {1} ({2}), {3}>".format(
            self.__class__.__name__,
            self.name,
            self.id,
            super().__repr__(),
        )

    @abc.abstractmethod
    async def connect(self, **kwargs) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    async def disconnect(self) -> bool:
        raise NotImplementedError()

    @property
    def is_connected(self) -> bool:
        raise NotImplementedError()

    @property
    def id(self) -> str:
        raise NotImplementedError()

    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def raw(self):
        raise NotImplementedError()

    @abc.abstractmethod
    async def send_command(self, data: TrainBlePacket) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def set_response_listener(self, callback: Callable[[TrainBlePacket], None]) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def set_disconnect_listener(self, callback: Callable[[], None]) -> None:
        raise NotImplementedError()
