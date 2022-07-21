import logging
from logging import Handler
from .ui import print_formatted as print


# Use the same formatting classes as defined in ui.py, to use prompt_toolkit for coloring output.
# Requires the PTKHandler to make use of it.
class CustomFormatter(logging.Formatter):
    format_message = "%(message)s"

    FORMATS = {
        logging.DEBUG: "class:debug",
        logging.INFO: "class:info",
        logging.WARNING: "class:warning",
        logging.ERROR: "class:error",
        logging.CRITICAL: "class:critical"
    }

    def format(self, record):
        style = self.FORMATS.get(record.levelno)
        if "style" in record.__dict__:
            style = record.__dict__["style"]
        formatter = logging.Formatter(self.format_message)
        return formatter.format(record), style


class PTKHandler(Handler):
    """
    A handler class which writes logging records, appropriately formatted, to prompt-toolkit print statements
    """
    def __init__(self, stream=None):
        Handler.__init__(self)

    def emit(self, record):
        """
        Emit a record.
        """
        try:
            text, style = self.format(record)
            print(text, style_class=style)
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)
