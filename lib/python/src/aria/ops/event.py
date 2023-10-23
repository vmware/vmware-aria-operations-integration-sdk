#  Copyright 2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Criticality(Enum):
    NONE = 0
    INFO = 1
    WARNING = 2
    IMMEDIATE = 3
    CRITICAL = 4
    AUTOMATIC = 5


@dataclass(frozen=True)
class Event:
    """
    Represents an Aria Operations Event.

    Args:
        message (str): The message describes and identifies an event.
        criticality (Criticality, optional): The criticality or severity of the event.
        fault_key (str, optional): A metric/property key that this event is related to. Defaults to None, which
                                   indicates the event's source is not related to a metric or property.
        auto_cancel (bool, optional): If True, VMware Aria Operations should automatically cancel an event
                                      when it stops being sent. Otherwise, it is the responsibility of the adapter
                                      to send the event with a 'cancel_date' when the event should be canceled.
                                      Defaults to True.
        start_date (int, optional): If set, overrides the start date of the event. Defaults to None, which indicates
                                    the start time should be the time when VMware Aria Operations first sees the event.
        update_date (int, optional): If set, indicates that the event has been updated by the target at the
                                     indicated time. Defaults to None.
        cancel_date (int, optional): If 'auto_cancel' is set to False, use the cancel_date to indicate that the event should
                                     be cancelled. Defaults to None.
        watch_wait_cycle (int, optional): The number of times this event must be present in a collection before Aria
                                          Operations surfaces it in the UI. Defaults to 1.
        cancel_wait_cycle (int, optional): If 'auto_cancel' is set to True, sets the number of times this event must be
                                           absent in a collection before Aria Operations removes it from the UI.
                                           Defaults to 3.
    """

    message: str
    criticality: Criticality = Criticality.NONE
    fault_key: Optional[str] = None
    auto_cancel: bool = True
    start_date: Optional[int] = None
    update_date: Optional[int] = None
    cancel_date: Optional[int] = None
    watch_wait_cycle: int = 1
    cancel_wait_cycle: int = 3

    def get_json(self) -> dict:
        """
        Get a JSON representation of this Event.

        Returns a JSON representation of this Event in the format required by Aria Operations.

        Returns:
            dict: A JSON representation of this Event.
        """
        # message is the only required field. Other fields are optional but non-nullable if present
        json: dict = {"message": self.message}

        if self.criticality is not None:
            json["criticality"] = self.criticality.value
        if self.message is not None:
            json["message"] = self.message
        if self.fault_key is not None:
            json["faultKey"] = self.fault_key
        if self.auto_cancel is not None:
            json["autoCancel"] = self.auto_cancel
        if self.start_date is not None:
            json["startDate"] = self.start_date
        if self.update_date is not None:
            json["updateDate"] = self.update_date
        if self.cancel_date is not None:
            json["cancelDate"] = self.cancel_date
        if self.watch_wait_cycle is not None:
            json["watchWaitCycle"] = self.watch_wait_cycle
        if self.cancel_wait_cycle is not None:
            json["cancelWaitCycle"] = self.cancel_wait_cycle

        return json
