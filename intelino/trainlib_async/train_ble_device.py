# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""train_ble_device.py"""

import asyncio
from asyncio.futures import Future
from rx.subject import BehaviorSubject, Subject
from rx.scheduler.eventloop import AsyncIOThreadSafeScheduler
from rx import operators as ops

from .drivers.train_ble_driver import TrainBleDriver
from .train_ble_packet import TrainBlePacket


class TrainBleDevice:
    """Train BLE Device."""

    def __init__(self, driver: TrainBleDriver):
        self._driver: TrainBleDriver = driver

        self.__connection_status: BehaviorSubject[bool] = BehaviorSubject(False)
        self.__notifications: Subject[TrainBlePacket, TrainBlePacket] = Subject()
        self.__writes: Subject[TrainBlePacket, TrainBlePacket] = Subject()

        driver.set_response_listener(self.__notifications.on_next)
        driver.set_disconnect_listener(lambda: self.__connection_status.on_next(False))

    @property
    def id(self) -> str:
        """Connection ID / address."""
        return self._driver.id

    @property
    def name(self) -> str:
        """Advertised name."""
        return self._driver.name

    @property
    def connection_status(self):
        scheduler = AsyncIOThreadSafeScheduler(asyncio.get_event_loop())
        return self.__connection_status.pipe(
            ops.as_observable(),
            ops.observe_on(scheduler),
            ops.subscribe_on(scheduler),
            ops.distinct_until_changed(),
        )

    @property
    def is_connected(self) -> bool:
        return self.__connection_status.value

    @property
    def notifications(self):
        scheduler = AsyncIOThreadSafeScheduler(asyncio.get_event_loop())
        return self.__notifications.pipe(
            ops.as_observable(),
            ops.observe_on(scheduler),
            ops.subscribe_on(scheduler),
        )

    @property
    def writes(self):
        scheduler = AsyncIOThreadSafeScheduler(asyncio.get_event_loop())
        return self.__writes.pipe(
            ops.as_observable(),
            ops.observe_on(scheduler),
            ops.subscribe_on(scheduler),
        )

    async def connect(self, force: bool = False, **kwargs):
        if self.is_connected and not force:
            return True

        connected = await self._driver.connect(**kwargs)
        self.__connection_status.on_next(connected)
        return connected

    async def disconnect(self):
        disconnected = await self._driver.disconnect()
        self.__connection_status.on_next(not disconnected)
        return disconnected

    async def send_command(self, data: TrainBlePacket):
        await self._driver.send_command(data)
        self.__writes.on_next(data)

    async def send_command_with_response(
        self, data: TrainBlePacket, timeout: float = 3.0
    ) -> TrainBlePacket:
        """Send a command and wait for a response from the train with a timeout.

        Raises:
            asyncio.exceptions.TimeoutError
        """

        future: Future[TrainBlePacket] = asyncio.Future()

        def on_error(err):
            print("Error: TrainBleDevice.send_command_with_response", err)
            pass

        self.__notifications.pipe(
            ops.take_until_with_time(timeout),
            ops.first(lambda packet: packet.command == data.command),
        ).subscribe(future.set_result, on_error=on_error)

        await self.send_command(data)
        return await asyncio.wait_for(future, timeout)
