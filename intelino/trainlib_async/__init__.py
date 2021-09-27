# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""
There are two variants of the **intelino trainlib**:

- Asynchronous library ``intelino-trainlib-async`` that uses the import
  ``intelino.trainlib_async``.
- Synchronous (blocking) ``intelino-trainlib`` that uses the import
  ``intelino.trainlib``.

They are very similar and share most of the code. The difference is mostly in
the :class:`TrainScanner` and :class:`Train` classes.
"""

from .train import Train
from .train_scanner import TrainScanner


__version__ = "1.0.1"
