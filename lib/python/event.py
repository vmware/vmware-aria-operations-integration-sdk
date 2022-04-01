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
    def __init__(self, message: str,
                 criticality: Criticality = Criticality.NONE,
                 fault_key: str = None,
                 auto_cancel: bool = False,
                 start_date: int = None,
                 update_date: int = None,
                 cancel_date: int = None,
                 watch_wait_cycle: int = 1,
                 cancel_wait_cycle: int = 3):
        self.criticality = criticality
        self.message = message
        self.fault_key = fault_key
        self.auto_cancel = auto_cancel
        self.start_date = start_date
        self.update_date = update_date
        self.cancel_date = cancel_date
        self.watch_wait_cycle = watch_wait_cycle
        self.cancel_wait_cycle = cancel_wait_cycle

    def get_json(self):
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
