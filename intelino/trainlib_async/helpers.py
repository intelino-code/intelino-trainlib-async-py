# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""helpers.py"""

import asyncio
import inspect
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Generic,
    Optional,
    TypeVar,
    Union,
)
from typing_extensions import ParamSpec, TypeGuard
from rx import typing
from rx.core.observer.observer import Observer


_P = ParamSpec("_P")
_T = TypeVar("_T")


def is_coroutine_function(
    callback: Callable[_P, Union[_T, Awaitable[_T]]],
) -> TypeGuard[Callable[_P, Awaitable[_T]]]:
    return inspect.iscoroutinefunction(callback)


def is_not_coroutine_function(
    callback: Callable[_P, Union[_T, Awaitable[_T]]],
) -> TypeGuard[Callable[_P, _T]]:
    return not inspect.iscoroutinefunction(callback)


AsyncOnNext = Callable[[_T], Coroutine[Any, Any, None]]
AsyncOnError = Callable[[Exception], Coroutine[Any, Any, None]]
AsyncOnCompleted = Callable[[], Coroutine[Any, Any, None]]


class AsyncObserver(Observer, Generic[_T]):
    """Observer implementation that accepts async functions as callbacks
    wrapping them in ``asyncio.create_task``.
    """

    def __init__(
        self,
        on_next: Optional[Union[typing.OnNext, AsyncOnNext[_T]]] = None,
        on_error: Optional[Union[typing.OnError, AsyncOnError]] = None,
        on_completed: Optional[Union[typing.OnCompleted, AsyncOnCompleted]] = None,
    ) -> None:
        def wrap(func: Callable[_P, Awaitable[None]]):
            def wrapped_func(*args: _P.args, **kwargs: _P.kwargs):
                try:
                    asyncio.get_running_loop()
                    asyncio.create_task(func(*args, **kwargs))

                except RuntimeError:
                    # if there is no running asyncio loop
                    asyncio.run(func(*args, **kwargs))

            return wrapped_func

        # synchronous version
        sync_on_next: Optional[typing.OnNext] = None
        sync_on_error: Optional[typing.OnError] = None
        sync_on_completed: Optional[typing.OnCompleted] = None

        if on_next:
            if is_coroutine_function(on_next):
                sync_on_next = wrap(on_next)
            elif is_not_coroutine_function(on_next):
                sync_on_next = on_next

        if on_error:
            if is_coroutine_function(on_error):
                sync_on_error = wrap(on_error)
            elif is_not_coroutine_function(on_error):
                sync_on_error = on_error

        if on_completed:
            if is_coroutine_function(on_completed):
                sync_on_completed = wrap(on_completed)
            elif is_not_coroutine_function(on_completed):
                sync_on_completed = on_completed

        super().__init__(sync_on_next, sync_on_error, sync_on_completed)
