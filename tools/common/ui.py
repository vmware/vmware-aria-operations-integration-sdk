from __future__ import unicode_literals

import os

from prompt_toolkit import prompt as tkprompt
from prompt_toolkit.application import Application
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.filters import IsDone, Filter, Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, FormattedTextControl
from prompt_toolkit.layout.containers import HSplit, Window, ConditionalContainer
from prompt_toolkit.layout.dimension import LayoutDimension, Dimension
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, TextArea

style = Style.from_dict({
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
})


def print_formatted(text, style_class="", frame=False):
    if frame:
        print_container(Frame(TextArea(text=text, wrap_lines=True), style=style_class), style=style)
    else:
        print_container(TextArea(text=text, style=style_class, wrap_lines=True), style=style)


class ListControlBase(FormattedTextControl):
    def __init__(self, message, description, items, selected_character):
        self.highlight_index = 0
        self.completed = False
        self.message = message
        self.description = description
        self.items = items
        self.selected_character = selected_character
        super().__init__(self._build_list, show_cursor=False)

    def _inc(self, amt):
        self.highlight_index = (self.highlight_index + amt) % len(self.items)

    # Override this in derived classes if necessary
    def _toggle_current(self):
        pass

    # Override this in derived classes
    def _get_selection(self):
        return []

    # Override this in derived classes
    def _is_selected(self, index):
        return False

    # Override this in derived classes if necessary
    def _is_disabled(self, index):
        return False

    def _bindings(self):
        bindings = KeyBindings()

        @bindings.add("c-q", eager=True)
        @bindings.add("c-c", eager=True)
        @bindings.add("c-d", eager=True)
        def _(event):
            event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

        @bindings.add("down", eager=True)
        def _down(event):
            self._inc(1)
            while self._is_disabled(self.highlight_index):
                self._inc(1)

        @bindings.add("up", eager=True)
        def _up(event):
            self._inc(-1)
            while self._is_disabled(self.highlight_index):
                self._inc(-1)

        @bindings.add("space", eager=True)
        def select(event):
            self._toggle_current()

        @bindings.add("enter", eager=True)
        def _select(event):
            self.completed = True
            event.app.exit(result=[item[0] for item in self._get_selection()])

        return bindings

    def _build_list(self):
        tokens = []
        for index, item in enumerate(self.items):
            if self._is_selected(index):
                tokens.append(("", f" {self.selected_character} "))
            else:
                tokens.append(("", "   "))

            if self._is_disabled(index):
                tokens.append(("class:disabled", f"{item[1]} ({item[2]})"))
            else:
                highlighted = (index == self.highlight_index)
                tokens.append(("class:selected" if highlighted else "", str(item[1])))
            tokens.append(("", "\n"))

        return tokens

    def _get_layout(self):
        def build_prompt():
            tokens = [("class:message", f"{self.message} ")]

            if self.completed:
                if len(self._get_selection()) == 1:
                    tokens.append(("class:answer", str(self._get_selection()[0][1])))
                else:
                    tokens.append(("class:answer", str([item[1] for item in self._get_selection()])))
            else:
                tokens.append(("", ""))
            return tokens

        @Condition
        def has_description():
            return bool(self.description)

        return Layout(HSplit([
            Window(height=LayoutDimension.exact(1), content=FormattedTextControl(build_prompt, show_cursor=False)),
            ConditionalContainer(
                Window(self),
                filter=~IsDone()
            ),
            ConditionalContainer(
                Window(
                    FormattedTextControl(
                        lambda: self.description, style="class:bottom-toolbar.text"
                    ),
                    style="class:bottom-toolbar",
                    wrap_lines=True,
                    height=Dimension(min=1),
                ),
                filter=~IsDone() & has_description
            )
        ]))

    def run(self):
        return Application(
            layout=self._get_layout(),
            key_bindings=self._bindings(),
            style=style
        ).run()


class SelectControl(ListControlBase):
    def __init__(self, message, description, items):
        super().__init__(message, description, items, "\u276f")

    def _get_selection(self):
        return [self.items[self.highlight_index]]

    def _is_selected(self, index):
        return index == self.highlight_index

    def _is_disabled(self, index):
        return self.items[index][2]


class MultiSelectControl(ListControlBase):
    def __init__(self, message, description, items):
        self.selected = [item[2] for item in items]
        super().__init__(message, description, items, "\u2713")

    def _get_selection(self):
        return [item for index, item in enumerate(self.items) if self.selected[index]]

    def _is_selected(self, index):
        return self.selected[index]

    # MultiSelect does not support disabling options currently
    def _is_disabled(self, index):
        return False

    def _toggle_current(self):
        self.selected[self.highlight_index] = not self.selected[self.highlight_index]


def selection_prompt(message, items, description=""):
    """
    :param message: Question/prompt to display above list of choices
    :param items: 2-tuples (key, label) or 3-tuples (key, label, disabled_message) that the user can select between
    :param description: Optional long description for the prompt with further details about the prompt message.
    :return key of selected item
    """
    items = list(map(lambda item: item if len(item) == 3 else (item[0], item[1], False), items))
    return SelectControl(message, description, items).run()[0]


def multiselect_prompt(message, items, description=""):
    """
    :param message: Question/prompt to display above list of choices
    :param items: 2-tuples (key, label) or 3-tuples (key, label, checked_by_default) the user can individually toggle
    :param description: Optional long description for the prompt with further details about the prompt message.
    :return list of keys of selected item(s)
    """
    items = list(map(lambda item: item if len(item) == 3 else (item[0], item[1], False), items))
    return MultiSelectControl(message, description, items).run()


def path_prompt(message, validator, description=""):
    """
    :param message: Question/prompt to display
    :param validator: Validator that determines if entered path is valid
    :param description: Optional long description for the prompt with further details about the prompt message.
    :return: absolute path that conforms to the validator
    """
    path = prompt(message,
                  description=description,
                  validator=validator,
                  validate_while_typing=False,
                  completer=PathCompleter(expanduser=True),
                  complete_in_thread=True)
    if path == "":
        return ""
    else:
        return os.path.abspath(os.path.expanduser(path))


def prompt(message, *args, description="", **kwargs) -> str:
    """
    Wrapper around the default prompt_toolkit prompt, with some defaults to make it match the other UI elements
    :param message: Question/prompt to display
    :param description: Optional long description for the prompt with further details about the prompt message.
    :return: User input
    """
    description = [("", description)] if description else None
    return tkprompt(message, *args, **kwargs,
                    bottom_toolbar=description,
                    lexer=SimpleLexer('class:answer'),
                    style=style)
