#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from aria.ops.event import Criticality
from aria.ops.event import Event


def test_minimal_event() -> None:
    event = Event("name", Criticality.CRITICAL)
    assert event.get_json() == {
        "message": "name",
        "criticality": 4,
        "autoCancel": True,
        "watchWaitCycle": 1,
        "cancelWaitCycle": 3,
    }
