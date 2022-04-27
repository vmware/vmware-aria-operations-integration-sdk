__author__ = 'VMware, Inc.'
__copyright__ = 'Copyright 2022 VMware, Inc. All rights reserved.'

from enum import Enum


class Criticality(Enum):
    NONE = 0
    INFO = 1
    WARNING = 2
    IMMEDIATE = 3
    CRITICAL = 4
    AUTOMATIC = 5


class Event:
    """ Represents a vROps Event

    """

    def __init__(self, message: str,
                 criticality: Criticality = Criticality.NONE,
                 fault_key: str = None,
                 auto_cancel: bool = False,
                 start_date: int = None,
                 update_date: int = None,
                 cancel_date: int = None,
                 watch_wait_cycle: int = 1,
                 cancel_wait_cycle: int = 3):
        """ Initialize a vROps Event

        :param message: The message describes and identifies an event.
        :param criticality: TODO
        :param fault_key: TODO
        :param auto_cancel: TODO
        :param start_date: TODO
        :param update_date: TODO
        :param cancel_date: TODO
        :param watch_wait_cycle: The number of times this event must be present in a collection before vROps surfaces it
            in the UI.
        :param cancel_wait_cycle: The number of times this event must be absent in a collection before vROps removes it
            from the UI.
        """
        self.message = message
        self.criticality = criticality
        self.fault_key = fault_key
        self.auto_cancel = auto_cancel
        self.start_date = start_date
        self.update_date = update_date
        self.cancel_date = cancel_date
        self.watch_wait_cycle = watch_wait_cycle
        self.cancel_wait_cycle = cancel_wait_cycle

    def get_json(self):
        """ Get a JSON representation of this Event.

        Returns a JSON representation of this Event in the format required by vROps.

        :return: A JSON representation of this Event.
        """
        return {
            "criticality": self.criticality,
            "message": self.message,
            "faultKey": self.fault_key,
            "autoCancel": self.auto_cancel,
            "startDate": self.start_date,
            "updateDate": self.update_date,
            "cancelDate": self.cancel_date,
            "watchWaitCycle": self.watch_wait_cycle,
            "cancelWaitCycle": self.cancel_wait_cycle
        }
