# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""internals.py - Internal enums."""

from enum import IntFlag


class StreamingRequestFlags(IntFlag):
    """Internal flags for streaming command (e.g. 0xB7)"""

    EMPTY = 0b000
    GET_ONCE = 0b000
    NO_RESPONSE = 0b001
    UPDATE_STREAMING_STATUS = 0b100
    STREAMING_START = 0b010 | UPDATE_STREAMING_STATUS
    STREAMING_STOP = 0b000 | UPDATE_STREAMING_STATUS


class RGBLedGroupId(IntFlag):
    TOP = 0b001
    FRONT = 0b010
    REAR = 0b100


class BehaviorFeedback(IntFlag):
    EMPTY = 0
    NO_FEEDBACK = 0
    # All feedback kinds on (default) - means “all” only if this bit alone is set.
    ALL = 0b0001
    SOUND = 0b0010
    LIGHTS = 0b0100
