#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from __future__ import unicode_literals

import logging
import os
import re
import sys
import time
from types import TracebackType
from typing import Any
from typing import Generic
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import Union

from prompt_toolkit import print_formatted_text
from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.application import application
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.filters import Condition
from prompt_toolkit.filters import IsDone
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding import KeyPressEvent
from prompt_toolkit.layout import FormattedTextControl
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator
from prompt_toolkit.widgets import Frame
from prompt_toolkit.widgets import TextArea

from vmware_aria_operations_integration_sdk.threading import threaded

logger = logging.getLogger(__name__)

TTL = True

style = Style.from_dict(
    {
        # Prompts
        "disabled": "fg:ansidarkgray italic",
        "selected": "reverse",
        "message": "",
        "answer": "fg:ansidarkgreen",
        "bottom-toolbar": "noreverse bg:ansiyellow fg:ansiblack",  # 'bottom-toolbar' is 'reverse' by default
        # Log message defaults
        "debug": "fg:ansidarkgray",
        "info": "",
        "warning": "fg:ansiyellow",
        "error": "fg:ansired",
        "critical": "fg:ansired bold",
        # Misc messages in UI
        "information": "bg:ansiblue fg:ansiblack",
        "important": "bg:ansidarkred fg:ansiblack",
        "success": "fg:ansigreen",
    }
)

FULL_WIDTH = "FULL_WIDTH"


def print_formatted(
    text: str = "", style_class: str = "", frame: Union[bool, str] = False
) -> None:
    if frame == FULL_WIDTH:
        print_container(
            TextArea(text=text, wrap_lines=True, style=style_class), style=style
        )
    elif frame:
        print_container(
            Frame(TextArea(text=text, wrap_lines=True), style=style_class), style=style
        )
    else:
        print_formatted_text(FormattedText([(style_class, text)]), style=style)


class ListControlBase(FormattedTextControl):  # type: ignore
    def __init__(
        self,
        message: str,
        description: str,
        items: List[Tuple],
        selected_character: str,
    ) -> None:
        self.highlight_index = 0
        self.completed = False
        self.message = message
        self.description = description
        self.items = items
        self.selected_character = selected_character
        super().__init__(self._build_list, show_cursor=False)

    def _inc(self, amt: int) -> None:
        self.highlight_index = (self.highlight_index + amt) % len(self.items)

    # Override this in derived classes if necessary
    def _toggle_current(self) -> None:
        pass

    # Override this in derived classes
    def _get_selection(self) -> List:
        return []

    # Override this in derived classes
    def _is_selected(self, index: int) -> bool:
        return False

    # Override this in derived classes if necessary
    def _is_disabled(self, index: int) -> bool:
        return False

    def _bindings(self) -> KeyBindings:
        bindings = KeyBindings()

        @bindings.add("c-q", eager=True)  # type: ignore
        @bindings.add("c-c", eager=True)  # type: ignore
        @bindings.add("c-d", eager=True)  # type: ignore
        def _(event: KeyPressEvent) -> None:
            event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

        @bindings.add("down", eager=True)  # type: ignore
        def _down(event: KeyPressEvent) -> None:
            self._inc(1)
            while self._is_disabled(self.highlight_index):
                self._inc(1)

        @bindings.add("up", eager=True)  # type: ignore
        def _up(event: KeyPressEvent) -> None:
            self._inc(-1)
            while self._is_disabled(self.highlight_index):
                self._inc(-1)

        @bindings.add("space", eager=True)  # type: ignore
        def select(event: KeyPressEvent) -> None:
            self._toggle_current()

        @bindings.add("enter", eager=True)  # type: ignore
        def _select(event: KeyPressEvent) -> None:
            self.completed = True
            event.app.exit(result=[item[0] for item in self._get_selection()])

        return bindings

    def _build_list(self) -> List:
        tokens = []
        for index, item in enumerate(self.items):
            if self._is_selected(index):
                tokens.append(("", f" {self.selected_character} "))
            else:
                tokens.append(("", "   "))

            if self._is_disabled(index):
                tokens.append(("class:disabled", f"{item[1]} ({item[2]})"))
            else:
                highlighted = index == self.highlight_index
                tokens.append(("class:selected" if highlighted else "", str(item[1])))
            tokens.append(("", "\n"))

        return tokens

    def _get_layout(self) -> Layout:
        def build_prompt() -> List[Tuple[str, str]]:
            tokens = [("class:message", f"{self.message} ")]

            if self.completed:
                if len(self._get_selection()) == 1:
                    tokens.append(("class:answer", str(self._get_selection()[0][1])))
                else:
                    tokens.append(
                        (
                            "class:answer",
                            str([item[1] for item in self._get_selection()]),
                        )
                    )
            else:
                tokens.append(("", ""))
            return tokens

        @Condition  # type: ignore
        def has_description() -> bool:
            return bool(self.description)

        return Layout(
            HSplit(
                [
                    Window(
                        height=LayoutDimension.exact(1),
                        content=FormattedTextControl(build_prompt, show_cursor=False),
                    ),
                    ConditionalContainer(Window(self), filter=~IsDone()),
                    ConditionalContainer(
                        Window(
                            FormattedTextControl(
                                lambda: self.description,
                                style="class:bottom-toolbar.text",
                            ),
                            style="class:bottom-toolbar",
                            wrap_lines=True,
                            height=Dimension(min=1),
                        ),
                        filter=~IsDone() & has_description,
                    ),
                ]
            )
        )

    def run(self) -> application._AppResult:
        return Application(
            layout=self._get_layout(), key_bindings=self._bindings(), style=style
        ).run(in_thread=True)


class SelectControl(ListControlBase):
    def __init__(self, message: str, description: str, items: List) -> None:
        if not TTL:
            raise Exception(
                f"TTL is not set: '{message}' must be a command line argument"
            )
        super().__init__(message, description, items, "\u276f")

    def _get_selection(self) -> List:
        return [self.items[self.highlight_index]]

    def _is_selected(self, index: int) -> bool:
        return index == self.highlight_index

    def _is_disabled(self, index: int) -> bool:
        return self.items[index][2]  # type: ignore


class MultiSelectControl(ListControlBase):
    def __init__(self, message: str, description: str, items: List[Tuple]) -> None:
        if not TTL:
            raise Exception(
                f"TTL is not set: '{message}' must be a command line argument"
            )
        self.selected: List[bool] = [item[2] for item in items]
        super().__init__(message, description, items, "\u2713")

    def _get_selection(self) -> List:
        return [item for index, item in enumerate(self.items) if self.selected[index]]

    def _is_selected(self, index: int) -> bool:
        return self.selected[index]

    # MultiSelect does not support disabling options currently
    def _is_disabled(self, index: int) -> bool:
        return False

    def _toggle_current(self) -> None:
        self.selected[self.highlight_index] = not self.selected[self.highlight_index]


def selection_prompt(
    message: str,
    items: Sequence[Tuple],
    description: str = "",
) -> Any:
    """
    :param message: Question/prompt to display above list of choices
    :param items: 2-tuples (key, label) or 3-tuples (key, label, disabled_message) that the user can select between
    :param description: Optional long description for the prompt with further details about the prompt message.
    :return key of selected item
    """
    expanded_items = list(
        map(lambda item: item if len(item) == 3 else (item[0], item[1], False), items)
    )
    return SelectControl(message, description, expanded_items).run()[0]


def multiselect_prompt(
    message: str,
    items: Sequence[Tuple],
    description: str = "",
) -> List[str]:
    """
    :param message: Question/prompt to display above list of choices
    :param items: 2-tuples (key, label) or 3-tuples (key, label, checked_by_default) the user can individually toggle
    :param description: Optional long description for the prompt with further details about the prompt message.
    :return list of keys of selected item(s)
    """
    expanded_items = list(
        map(lambda item: item if len(item) == 3 else (item[0], item[1], False), items)
    )
    return MultiSelectControl(message, description, expanded_items).run()  # type: ignore


def path_prompt(message: str, validator: Validator, description: str = "") -> str:
    """
    :param message: Question/prompt to display
    :param validator: Validator that determines if entered path is valid
    :param description: Optional long description for the prompt with further details about the prompt message.
    :return: absolute path that conforms to the validator
    """
    path = prompt(
        message,
        description=description,
        validator=validator,
        validate_while_typing=False,
        completer=PathCompleter(expanduser=True),
        complete_in_thread=True,
    )
    if path == "":
        return ""
    else:
        return os.path.abspath(os.path.expanduser(path))


def prompt(message: str, *args: Any, description: str = "", **kwargs: Any) -> str:
    """
    Wrapper around the default prompt_toolkit prompt, with some defaults to make it match the other UI elements
    :param message: Question/prompt to display
    :param description: Optional long description for the prompt with further details about the prompt message.
    :return: User input
    """
    if not TTL:
        raise Exception(f"TTL is not set: '{message}' must be a command line argument")
    session: PromptSession[str] = PromptSession()

    return session.prompt(  # type: ignore
        message,
        *args,
        **kwargs,
        bottom_toolbar=[("", description)] if description else None,
        lexer=SimpleLexer("class:answer"),
        style=style,
        in_thread=True,
    )


class Spinner:
    def __init__(self, text: str):
        self.text = text
        self.spinner = None
        if TTL:
            self.spinner = _Spinner(text)

    def __enter__(self) -> Spinner:
        if self.spinner:
            self.spinner.__enter__()
        else:
            logger.info(f"Starting {self.text}")
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_value: Optional[BaseException] = None,
        traceback: Optional[TracebackType] = None,
    ) -> None:
        if self.spinner:
            self.spinner.__exit__(exc_type, exc_value, traceback)
        else:
            logger.info(f"Finished {self.text}")


class _Spinner(FormattedTextControl):  # type: ignore
    def __init__(self, text: str) -> None:
        self.spinner_text = text
        self._index = 0
        self._update_time = time.time()
        self._finished = False
        super().__init__()

    def __enter__(self) -> _Spinner:
        self.application = Application(
            layout=self._get_layout(),
            key_bindings=self._bindings(),
            style=style,
            refresh_interval=0.1,
        )
        self._application_task = self._start_application()
        while not self.application.is_running:
            pass
        return self

    @threaded
    def _start_application(self) -> None:
        self.application.run()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_value: Optional[BaseException] = None,
        traceback: Optional[TracebackType] = None,
    ) -> None:
        self._finished = True

        # The spinner *should* be running when we get here. If it's not, it's because the user interrupted with ctrl-c
        # or similar. We don't need to call application.exit(), because it's already stopped, but we *do* need to
        # re-raise the exception, as it was raised on the spinner thread and not the main thread.
        if not self.application.is_running:
            raise KeyboardInterrupt("Cancelled")

        self.application.exit()
        # we've called exit, now have to wait for task to finish
        # weird things can happen if two applications are running at the same time; this will prevent that in the case
        # a spinner is started immediately after another
        while not self._application_task.done():
            pass

    def _get_layout(self) -> Layout:
        def get_text() -> List[Tuple]:
            spinner = "-\\|/"[self._index]
            if time.time() >= self._update_time + 0.2:
                self._index = (self._index + 1) % 4
                self._update_time = time.time()

            if not self._finished and not sys.stdout.isatty():
                return [("class:message", self.spinner_text)]
            elif not self._finished:
                return [("class:message", self.spinner_text + " " + spinner)]
            else:
                return [
                    ("class:message", self.spinner_text + " "),
                    ("class:answer", "[Finished]"),
                ]

        return Layout(
            HSplit(
                [
                    Window(
                        height=LayoutDimension.exact(1),
                        content=FormattedTextControl(get_text, show_cursor=False),
                    )
                ]
            )
        )

    def _bindings(self) -> KeyBindings:
        bindings = KeyBindings()

        @bindings.add("c-q", eager=True)  # type: ignore
        @bindings.add("c-c", eager=True)  # type: ignore
        @bindings.add("c-d", eager=True)  # type: ignore
        def _(event: KeyPressEvent) -> None:
            event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

        return bindings


def countdown(duration: float, message: str = "") -> None:
    end_time = time.time() + duration
    remaining = ""
    try:
        while time.time() < end_time:
            remaining = time.strftime("%H:%M:%S", time.gmtime(end_time - time.time()))
            print(f"{message}{remaining}", end="\r")
            time.sleep(0.2)

    finally:
        # Clears the last statement print statement
        print(re.sub("", " ", message + f"{remaining}"), end="\r")


class Table:
    def __init__(self, headers: List[Any], data: List[List[Any]]) -> None:
        # Convert each header/cell to a string - otherwise won't work with len() and format() functions
        self.headers = [str(header) for header in headers]
        self.data = [[str(col) for col in row] for row in data]

    def __repr__(self) -> str:
        output = ""
        column_sizes = []
        horizontal_rule = []
        for col in range(len(self.headers)):
            size = len(self.headers[col])
            for row in self.data:
                size = max(size, max([len(line) for line in row[col].splitlines()]))
            column_sizes.append("{:<" + str(size) + "}")
            horizontal_rule.append("-" * size)
        formatting = " | ".join(column_sizes)

        output += formatting.format(*self.headers) + "\n"
        output += "-+-".join(horizontal_rule) + "\n"
        for row in self.data:
            columns = [col.splitlines() for col in row]
            line_count = max(map(lambda _lines: len(_lines), columns))
            for line_number in range(line_count):
                line = map(
                    lambda column: ""
                    if line_number >= len(column)
                    else column[line_number],
                    columns,
                )
                output += formatting.format(*line) + "\n"

        return output
