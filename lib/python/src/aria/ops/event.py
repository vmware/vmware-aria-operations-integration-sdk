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
        criticality (Criticality, optional): TODO. Defaults to Criticality.NONE.
        fault_key (str, optional): TODO. Defaults to None.
        auto_cancel (bool, optional): TODO. Defaults to False.
        start_date (int, optional): TODO. Defaults to None.
        update_date (int, optional): TODO. Defaults to None.
        cancel_date (int, optional): TODO. Defaults to None.
        watch_wait_cycle (int, optional): The number of times this event must be present in a collection before Aria
                                          Operations surfaces it in the UI. Defaults to 1.
        cancel_wait_cycle (int, optional): The number of times this event must be absent in a collection before Aria
                                            Operations removes it from the UI. Defaults to 3.
    """

    message: str
    criticality: Criticality = Criticality.NONE
    fault_key: Optional[str] = None
    auto_cancel: bool = False
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
