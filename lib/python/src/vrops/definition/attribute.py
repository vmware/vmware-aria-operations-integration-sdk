#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from abc import ABC
from vrops.definition.units import Unit


class Attribute(ABC):
    def __init__(self,
                 key: str,
                 label: str,
                 unit: Unit = None,
                 dashboard_order: int = None,
                 is_rate: bool = False,
                 is_discrete: bool = False,
                 is_impact: bool = False,
                 dt_type: str = None,
                 is_key_attribute: bool = False):
        self.key = key
        self.label = label
        self.unit = unit.name if unit else None
        self.dashboard_order = dashboard_order
        self.is_rate = unit.value.is_rate if unit else is_rate
        self.is_discrete = is_discrete
        self.is_impact = is_impact
        self.dt_type = dt_type
        self.is_key_attribute = is_key_attribute

    def to_json(self):
        return {
            "key": self.key,
            "label": self.label,
            "unit": self.unit,
            "dashboard_order": self.dashboard_order,
            "is_rate": self.is_rate,
            "is_discrete": self.is_discrete,
            "is_impact": self.is_impact,
            "dt_type": self.dt_type,
            "is_key_attribute": self.is_key_attribute
        }


class MetricAttribute(Attribute):
    def __init__(self, key, *args, **kwargs):
        super().__init__(key, *args, **kwargs)

    def to_json(self):
        return super().to_json() | {
            "data_type": "integer" if self.is_discrete else "float",
            "is_property": False
        }


class PropertyAttribute(Attribute):
    def __init__(self, key, *args, is_string: bool = False, **kwargs):
        super().__init__(key, *args, **kwargs)
        self.is_string = is_string

    def to_json(self):
        return super().to_json() | {
            "data_type": "string" if self.is_string else "integer" if self.is_discrete else "float",
            "is_property": True
        }


