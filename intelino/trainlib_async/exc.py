# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""Exceptions"""


class TrainlibError(Exception):
    """Base error."""

    pass


class TrainNotFoundError(TrainlibError):
    """If the train we search for, or no train at all is found."""

    pass


class TrainNotConnectedError(TrainlibError):
    """In case the train disconnected or wasn't connected yet."""

    pass


class TrainMessageTypeError(TrainlibError):
    """Incorrect message type was expected."""

    pass


class TrainMessageLengthError(TrainlibError):
    """The length of the received message is shorter than expected and cannot be parsed."""

    pass


class TrainMessageInterpretationError(TrainlibError):
    """Structure unpacking failed."""

    pass


class TrainCommandError(TrainlibError):
    """Command building error."""

    pass
