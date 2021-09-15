# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""train_factory.py"""

import asyncio
from typing import List, Optional, Set, Union
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakError

from .train import Train
from .train_ble_device import TrainBleDevice
from .drivers.bleak_driver import BleakDriver


async def _find_trains_with_bleak(
    limit: int = None, timeout: float = 10.0, **kwargs
) -> List[BLEDevice]:
    stop_scanning_event = asyncio.Event()
    device_ids: Set[str] = set()

    def stop_if_detected_enough(d: BLEDevice, _: AdvertisementData):
        if d.name and d.name.lower().startswith("intelino"):
            device_ids.add(d.address)
            if limit and (len(device_ids) >= limit):
                stop_scanning_event.set()

    async with BleakScanner(
        timeout=timeout, detection_callback=stop_if_detected_enough, **kwargs
    ) as scanner:
        try:
            await asyncio.wait_for(stop_scanning_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass

        return [
            device
            for device in scanner.discovered_devices
            if device.address in device_ids
        ]


class TrainFactory:
    """Create train instances with the Bleak BLE library."""

    @staticmethod
    async def create_train(
        device_identifier: str = None, connect: bool = True, **kwargs
    ) -> Optional[Train]:
        """A convenience method for obtaining a ``Train`` object specified
        by a Bluetooth address or (on macOS) UUID address.

        Args:
            device_identifier (str): The Bluetooth/UUID address of the Bluetooth
                peripheral sought. If not specified, it will return the first
                found intelino train.
            connect (bool): Whether to auto-connect to the found train.
                Defaults to True.

        Keyword Args:
            name (str): Optional forced name for the device. If provided, name
                detection is skipped.
            timeout (float): Optional timeout to wait for detection of specified
                peripheral before giving up. Defaults to 10.0 seconds.
            adapter (str): Bluetooth adapter to use for discovery.

        Returns:
            The ``Train`` sought or ``None`` if not detected.

        """
        address = device_identifier
        name: Union[str, None] = kwargs.get("name")

        if device_identifier:
            if not name:
                device = await BleakScanner.find_device_by_address(
                    device_identifier, **kwargs
                )
                if not device:
                    return None

                name = device.name

        else:
            devices = await _find_trains_with_bleak(1, **kwargs)
            if len(devices) == 0:
                return None

            address = devices[0].address
            name = devices[0].name

        if not isinstance(address, str):
            return None

        driver = BleakDriver(address, name)
        train_device = TrainBleDevice(driver)
        train = Train(train_device)

        if connect:
            try:
                await train.connect(**kwargs)
            except BleakError:
                return None

        return train

    @staticmethod
    async def create_trains(
        count: int = None, timeout: float = 5.0, connect: bool = True, **kwargs
    ) -> List[Train]:
        """A convenience method for obtaining multiple ``Train`` objects.

        Args:
            count (int): Optional detection limit. If ommited or 0, it searches
                for all trains in the vicinity until it timeouts.
            timeout (float): Optional timeout to wait for detection. If the
                train count is satisfied sooner, it will not wait. Defaults
                to 5.0 seconds.
            connect (bool): Whether to auto-connect to the found trains.
                Defaults to True.

        Keyword Args:
            adapter (str): Bluetooth adapter to use for discovery.

        Returns:
            A list of ``Train`` instances.
        """
        trains: List[Train] = []
        devices = await _find_trains_with_bleak(count, timeout, **kwargs)

        for device in devices:
            try:
                driver = BleakDriver(device.address, device.name)
                train_device = TrainBleDevice(driver)
                train = Train(train_device)
                if connect:
                    await train.connect(**kwargs)
                trains.append(train)
            except BleakError:
                continue

        return trains
