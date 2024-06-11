#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from abc import ABC
from typing import Optional

from aria.ops.definition.assertions import validate_key
from aria.ops.definition.units import Unit


class Attribute(ABC):
    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        unit: Optional[Unit] = None,
        is_rate: bool = False,
        is_discrete: bool = False,
        is_kpi: bool = False,
        is_impact: bool = False,
        is_key_attribute: bool = False,
        dashboard_order: int = 0,
    ):
        """

        Args:
            key (str): Used to identify the parameter.
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            unit (Optional[str]): Specifies what unit this metric is returned in. This allows the UI to display the units in a
        consistent manner, and perform conversions when appropriate.
            is_rate (bool): Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
            will be set automatically. Otherwise, defaults to False.
            is_discrete (bool): Declares that this attribute's range of values is discrete (integer) rather than continuous
            (floating point). Defaults to False.
            is_kpi (bool): If set, threshold breaches for this metric will be used in the calculation of the object's
            'Self - Health Score' metric, which can affect the 'Anomalies' Badge. Defaults to False.
            is_impact (bool): If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
            proxy to a root cause, but not the root cause itself. Defaults to False.
            is_key_attribute (bool): True if the attribute should be shown in some object summary widgets in the UI.
            dashboard_order (int): Determines the order parameters will be displayed in the UI. Defaults to 0
        """
        self.key = validate_key(key, "Attribute")
        self.label = label
        if label is None:
            self.label = key
        self.unit = unit.value.key if unit else None
        self.is_rate = unit.value.is_rate if unit else is_rate
        self.is_discrete = is_discrete
        self.is_kpi = is_kpi
        self.is_impact = is_impact
        self.is_key_attribute = is_key_attribute
        self.dashboard_order = dashboard_order

    def to_json(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "unit": self.unit,
            "is_rate": self.is_rate,
            "is_discrete": self.is_discrete,
            "is_kpi": self.is_kpi,
            "is_impact": self.is_impact,
            "is_key_attribute": self.is_key_attribute,
            "dashboard_order": self.dashboard_order,
        }


class MetricAttribute(Attribute):
    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        unit: Optional[Unit] = None,
        is_rate: bool = False,
        is_discrete: bool = False,
        is_kpi: bool = False,
        is_impact: bool = False,
        is_key_attribute: bool = False,
        dashboard_order: int = 0,
    ):
        """

        Args:
            key (str): Used to identify the parameter.
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            unit (Optional[Unit]): Specifies what unit this metric is returned in. This allows the UI to display the units in a
                consistent manner, and perform conversions when appropriate.
            is_rate (bool): Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
                will be set automatically. Otherwise, defaults to False.
            is_discrete (bool): Declares that this attribute's range of values is discrete (integer) rather than continuous
                (floating point)
            is_kpi (bool): If set, threshold breaches for this metric will be used in the calculation of the object's
                'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
            is_impact (bool): If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
                proxy to a root cause, but not the root cause itself.
            is_key_attribute (bool): True if the attribute should be shown in some object summary widgets in the UI.
            dashboard_order (bool): Determines the order parameters will be displayed in the UI.
        """
        super().__init__(
            key,
            label,
            unit,
            is_rate,
            is_discrete,
            is_kpi,
            is_impact,
            is_key_attribute,
            dashboard_order,
        )

    def to_json(self) -> dict:
        return super().to_json() | {
            "data_type": "integer" if self.is_discrete else "float",
            "is_property": False,
        }


class PropertyAttribute(Attribute):
    def __init__(
        self,
        key: str,
        label: Optional[str] = None,
        is_string: bool = True,
        unit: Optional[Unit] = None,
        is_rate: bool = False,
        is_discrete: bool = False,
        is_kpi: bool = False,
        is_impact: bool = False,
        is_key_attribute: bool = False,
        dashboard_order: int = 0,
    ):
        """

        Args:
            key (str): Used to identify the parameter.
            label (Optional[str]): Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
            is_string (bool): Determines if the property is numeric or string (text).
            unit (Optional[Unit]): Specifies what unit this metric is returned in. This allows the UI to display the units in a
                consistent manner, and perform conversions when appropriate.
            is_rate (bool): Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
                will be set automatically. Otherwise, defaults to False.
            is_discrete (bool): Declares that this attribute's range of values is discrete (integer) rather than continuous
                (floating point). Defaults to False, unless 'is_string' is set, in which case it will always be set to True.
            is_kpi (bool): If set, threshold breaches for this metric will be used in the calculation of the object's
                'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
            is_impact (bool): If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
                proxy to a root cause, but not the root cause itself.
            is_key_attribute (bool): True if the attribute should be shown in some object summary widgets in the UI.
            dashboard_order (int): Determines the order parameters will be displayed in the UI.
        """
        super().__init__(
            key,
            label,
            unit,
            is_rate,
            is_discrete,
            is_kpi,
            is_impact,
            is_key_attribute,
            dashboard_order,
        )
        self.is_string = is_string

    def to_json(self) -> dict:
        return super().to_json() | {
            "data_type": (
                "string"
                if self.is_string
                else "integer" if self.is_discrete else "float"
            ),
            "is_discrete": True if self.is_string else self.is_discrete,
            "is_property": True,
        }
