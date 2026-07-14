from __future__ import annotations

import signal
from collections.abc import Iterator
from contextlib import contextmanager
from types import FrameType


class TerminationSignal(BaseException):
    """Request an orderly unwind before preserving a termination signal."""

    def __init__(self, signum: int) -> None:
        self.signum = signum
        super().__init__(signum)


@contextmanager
def termination_signals() -> Iterator[None]:
    """Turn supported process signals into an orderly stack unwind."""
    supported = (signal.SIGTERM, signal.SIGHUP)
    previous = {signum: signal.getsignal(signum) for signum in supported}

    def request_shutdown(signum: int, frame: FrameType | None) -> None:
        del frame
        raise TerminationSignal(signum)

    try:
        for signum in supported:
            signal.signal(signum, request_shutdown)
        yield
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
