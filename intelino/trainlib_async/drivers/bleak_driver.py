# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""bleak_driver.py"""

import asyncio
from bleak import BleakClient
from bleak.backends.device import BLEDevice
from typing import Awaitable, Callable, Union

from .train_ble_driver import TrainBleDriver
from ..helpers import is_not_coroutine_function, is_coroutine_function
from ..train_ble_packet import TrainBlePacket


class BleakDriver(TrainBleDriver):
    """Train BLE Driver using the Bleak BLE library."""

    def __init__(
        self, address_or_ble_device: Union[BLEDevice, str], name: str = None, **kwargs
    ):
        super().__init__()
        if isinstance(address_or_ble_device, BLEDevice) and name is None:
            self.__name: str = address_or_ble_device.name
        else:
            self.__name: str = name if name else "intelino J-1"

        self.__bleak_client: BleakClient = BleakClient(address_or_ble_device, **kwargs)
        self.__response_callback: Union[Callable[[TrainBlePacket], None], None] = None

    async def connect(self, **kwargs) -> bool:
        connected = await self.__bleak_client.connect(**kwargs)

        if connected:

            def callback(_: int, data: bytearray):
                if self.__response_callback:
                    self.__response_callback(TrainBlePacket(data))

            await self.__bleak_client.start_notify(
                self.RESPONSE_CHARACTERISTIC, callback
            )

        return connected and self.__bleak_client.is_connected

    async def disconnect(self) -> bool:
        if self.__bleak_client.is_connected:
            await self.__bleak_client.stop_notify(self.RESPONSE_CHARACTERISTIC)
        return await self.__bleak_client.disconnect()

    @property
    def is_connected(self) -> bool:
        return self.__bleak_client.is_connected

    @property
    def id(self) -> str:
        return self.__bleak_client.address

    @property
    def name(self) -> str:
        return self.__name

    @property
    def raw(self) -> BleakClient:
        return self.__bleak_client

    async def send_command(self, data: TrainBlePacket) -> None:
        if len(data.data) > 0:
            # NOTE: using write-with-response only to wait for the write to finish
            await self.__bleak_client.write_gatt_char(
                self.COMMAND_CHARACTERISTIC, data.data, True
            )

    def set_response_listener(
        self, callback: Callable[[TrainBlePacket], Union[None, Awaitable[None]]]
    ) -> None:
        if is_coroutine_function(callback):
            async_callback = callback

            def wrapped_callback(packet: TrainBlePacket):
                asyncio.create_task(async_callback(packet))

            self.__response_callback = wrapped_callback

        elif is_not_coroutine_function((callback)):
            self.__response_callback = callback

    def set_disconnect_listener(self, callback: Callable[[], None]) -> None:
        self.__bleak_client.set_disconnected_callback(lambda _: callback())
