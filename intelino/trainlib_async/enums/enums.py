# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""enums.py"""

import random
from enum import IntEnum, IntFlag
from typing import Tuple

from ..exc import TrainCommandError


class SnapColorValue(IntFlag):
    """Single snap color."""

    def __str__(self):
        return "{0}".format(self.name)

    def to_rgb_bytes(self) -> Tuple[int, int, int]:
        """Convert the color's value to 3 bytes (0-255) to form an RGB tuple."""
        red = 0
        green = 0
        blue = 0
        if self.value & SnapColorValue.RED:
            red = 255
        if self.value & SnapColorValue.GREEN:
            green = 255
        if self.value & SnapColorValue.BLUE:
            blue = 255

        return (red, green, blue)

    @classmethod
    def random(cls, including_black: bool = True):
        """Return a random color."""
        from_value = cls.BLACK if including_black else cls.RED
        to_value = cls.WHITE
        return cls(random.randint(from_value, to_value))

    BLACK = 0b000
    RED = 0b001
    GREEN = 0b010
    BLUE = 0b100
    YELLOW = RED | GREEN
    MAGENTA = RED | BLUE
    CYAN = GREEN | BLUE
    WHITE = RED | GREEN | BLUE
    UNKNOWN = 0b1000


class SpeedLevel(IntEnum):
    STOP = 0
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3


class _OldSteeringDecision(IntFlag):
    NONE = 0
    LEFT = 0b001
    RIGHT = 0b010
    CENTER = 0b011  # different!


class SteeringDecision(IntFlag):
    NONE = 0
    LEFT = 0b001
    RIGHT = 0b010
    STRAIGHT = 0b100
    STEER = LEFT | RIGHT
    ALL = LEFT | RIGHT | STRAIGHT


def _convert_to_old_steering_decision(decision: SteeringDecision):
    """Convert to the older version of steering decision."""
    if decision == SteeringDecision.LEFT:
        return _OldSteeringDecision.LEFT
    elif decision == SteeringDecision.RIGHT:
        return _OldSteeringDecision.RIGHT
    elif decision == SteeringDecision.STRAIGHT:
        return _OldSteeringDecision.CENTER
    else:
        raise TrainCommandError(f"Parameter {repr(decision)} is not supported!")


def _convert_from_old_steering_decision(decision: _OldSteeringDecision):
    """Convert to the new version of steering decision."""
    if decision == _OldSteeringDecision.NONE:
        return SteeringDecision.NONE
    elif decision == _OldSteeringDecision.LEFT:
        return SteeringDecision.LEFT
    elif decision == _OldSteeringDecision.RIGHT:
        return SteeringDecision.RIGHT
    elif decision == _OldSteeringDecision.CENTER:
        return SteeringDecision.STRAIGHT
    else:
        return SteeringDecision.NONE


class MovementDirection(IntEnum):
    # Maintain the current direction.
    CURRENT = 0
    FORWARD = 1
    BACKWARD = 2
    STOP = 3
    # Invert the current direction.
    INVERT = 4


class ButtonPress(IntEnum):
    SHORT = 1
    # After detecting a long press the train turns off.
    LONG = 2


class StopDrivingFeedbackType(IntEnum):
    """Used only with train.stopDriving() function."""

    NONE = 0
    MOVEMENT_STOP = 1
    END_ROUTE = 2

class ColorSensor(IntEnum):
    """Color sensor identification."""
    FRONT = 1
    BACK = 2
