# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""train_scanner.py - Simplified train scanning and instantiation."""

from typing import List

from .train import Train
from .train_factory import TrainFactory
from .exc import TrainNotFoundError


class TrainScanner:
    """Obtaining a ``Train`` object using the ``async with`` statement."""

    def __init__(self, device_identifier: str = None, timeout: float = 5.0):
        """
        Args:
            device_identifier (str): The Bluetooth/UUID address of the Bluetooth
                peripheral sought. If not specified, it will return the first
                found intelino train.
            timeout (float): Optional timeout to wait for detection of specified
                peripheral before giving up. Defaults to 5.0 seconds.
        """
        self.device_identifier = device_identifier
        self.timeout = timeout

    # Async Context managers

    async def __aenter__(self):
        self.train = await self.get_train()
        return self.train

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.train is not None:
            await self.train.disconnect()

    async def get_train(self, connect: bool = True, **kwargs) -> Train:
        """Get a train instance asynchronously.

        Args:
            connect (bool): Whether to auto-connect to the found train.
                Defaults to True.

        Keyword Args:
            adapter (str): Bluetooth adapter to use for discovery.

        Raises:
            TrainNotFoundError: If no train is found.

        Returns:
            A ``Train`` instance.
        """
        train = await TrainFactory.create_train(
            device_identifier=kwargs.pop("device_identifier", self.device_identifier),
            timeout=kwargs.pop("timeout", self.timeout),
            connect=connect,
            **kwargs,
        )

        if train is None:
            raise TrainNotFoundError("Train not found!")

        return train

    async def get_trains(
        self, count: int = None, connect: bool = True, **kwargs
    ) -> List[Train]:
        """Get a list of train instances asynchronously.

        Args:
            count (int): Optional detection limit. If ommited or 0, it searches
                for all trains in the vicinity until it timeouts.
            connect (bool): Whether to auto-connect to the found trains.
                Defaults to True.

        Keyword Args:
            at_most (int): Connect to at most N trains. No exception is raised
                if the `count` argument is omitted.
            adapter (str): Bluetooth adapter to use for discovery.

        Raises:
            TrainNotFoundError: If no train is found.

        Returns:
            A list of ``Train`` instances.
        """
        trains = await TrainFactory.create_trains(
            count=kwargs.pop("count", kwargs.pop("at_most", count)),
            connect=connect,
            timeout=kwargs.pop("timeout", self.timeout),
            **kwargs,
        )

        if count and (len(trains) != count):
            if connect:
                for train in trains:
                    await train.disconnect()
            raise TrainNotFoundError(
                f"Could not find all the requested trains (got {len(trains)} instead of {count})!"
            )

        return trains
