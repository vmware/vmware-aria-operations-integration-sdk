from __future__ import annotations

from logging import Logger
from time import time
from types import TracebackType
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type


class Timer:
    timers: List[Tuple[str, float, float]] = []

    def __init__(self, logger: Logger, name: str) -> None:
        self.logger = logger
        self.name = name

    def __enter__(self) -> Timer:
        self.logger.info(self.name)
        self.start_time = time()
        return self

    def __aenter__(self) -> Timer:
        self.logger.info(self.name)
        self.start_time = time()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_value: Optional[BaseException] = None,
        traceback: Optional[TracebackType] = None,
    ) -> None:
        end_time = time()
        self.timers.append((self.name, self.start_time, end_time))
        self.logger.info(f"finished {self.name} in {end_time - self.start_time:.2}s")

    def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_value: Optional[BaseException] = None,
        traceback: Optional[TracebackType] = None,
    ) -> None:
        end_time = time()
        self.timers.append((self.name, self.start_time, end_time))
        self.logger.info(f"finished {self.name} in {end_time - self.start_time:.2}s")

    @classmethod
    def graph(cls) -> str:
        headers = ["Operation", "Time"]
        full_headers = []
        width = 88
        time_min = time()
        time_max = 0.0
        name_max = len(headers[0])
        for name, start, end in cls.timers:
            if start < time_min:
                time_min = start
            if end > time_max:
                time_max = end
            if len(name) > name_max:
                name_max = len(name)

        graph_width = width - name_max - 10
        step = (time_max - time_min) / graph_width
        headers.append("t=0s")
        headers.append(f"t={_to_time(time_max - time_min)}")

        full_headers.append(f"{headers[0]:<{name_max}}")
        full_headers.append(f"{headers[1]:<8}")
        full_headers.append(
            f"{headers[2]:<{int(graph_width / 2)}}{headers[3]:>{int((graph_width + 1) / 2)}}"
        )

        sorted_intervals: Iterable[Tuple[str, float, float]] = sorted(
            cls.timers, key=lambda i: i[1]
        )
        graph = "Timing Graph: \n"
        graph += _hline(full_headers, "U")
        graph += "│".join(full_headers) + "\n"
        graph += _hline(full_headers)
        for name, start, end in sorted_intervals:
            graph += (
                f"{name:<{name_max}}│"
                f"{_to_time(end - start):<8}│"
                + _graph_timespan(
                    (start - time_min) / step, (end - time_min) / step, graph_width
                )
                + "\n"
            )
        graph += _hline(full_headers, "L")
        return graph


def _hline(headers: List, loc: str = "M") -> str:
    hl = ""
    for header in headers:
        for x in range(len(header)):
            hl += "━"
        if loc == "U":
            hl += "┯"
        elif loc == "M":
            hl += "┿"
        else:  # loc = L
            hl += "┷"
    return f"{hl[:-1]}\n"


def _graph_timespan(start: float, end: float, graph_width: int) -> str:
    line = ""

    def in_range(x_coord: float) -> bool:
        return start <= x_coord < end

    for x in range(graph_width):
        if in_range(x - 1) and in_range(x) and in_range(x + 1):
            line += "─"
        elif in_range(x - 1) and in_range(x):
            line += "╼"
        elif in_range(x) and in_range(x + 1):
            line += "╾"
        elif in_range(x):
            line += "━"
        else:
            line += " "
    return f"{line}"


def _to_time(seconds: float) -> str:
    if seconds > 3600:
        hours = seconds / 3600
        return f"{hours:.2f}h"
    elif seconds > 120:
        minutes = seconds / 60
        return f"{minutes:.2f}m"
    return f"{seconds:.2f}s"
