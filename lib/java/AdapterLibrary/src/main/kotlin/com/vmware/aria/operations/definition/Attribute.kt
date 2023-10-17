/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations.definition

import com.vmware.aria.operations.KeyException
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

/**
 * Args:
 * @param key Used to identify the parameter.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param unit Specifies what unit this metric is returned in. This allows the UI to display the units in a
 * consistent manner, and perform conversions when appropriate.
 * @param isRate Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
 * will be set automatically. Otherwise, defaults to False.
 * @param isDiscrete Declares that this attribute's range of values is discrete (integer) rather than continuous
 * (floating point). Defaults to False.
 * @param isKpi If set, threshold breaches for this metric will be used in the calculation of the object's
 * 'Self - Health Score' metric, which can affect the 'Anomalies' Badge. Defaults to False.
 * @param isImpact If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
 * proxy to a root cause, but not the root cause itself. Defaults to False.
 * @param isKeyAttribute True if the attribute should be shown in some object summary widgets in the UI.
 * @param dashboardOrder Determines the order parameters will be displayed in the UI. Defaults to 0
 */
sealed class Attribute @Throws(KeyException::class) @JvmOverloads constructor(
    val key: String,
    val label: String = key,
    val unit: SdkUnit = Units.None,
    val isRate: Boolean = unit.isRate,
    val isDiscrete: Boolean = false,
    val isKpi: Boolean = false,
    val isImpact: Boolean = false,
    val isKeyAttribute: Boolean = false,
    val dashboardOrder: Int = 0,
) {
    init {
        if (key.isBlank()) {
            throw KeyException("Attribute key cannot be empty.")
        }
    }
    private val unitKey = if (unit.key == Units.None.key) null else unit.key
    abstract val dataType: String
    abstract val isProperty: Boolean

    val json: JsonObject
        get() = buildJsonObject {
            put("key", key)
            put("label", label)
            put("unit", unitKey)
            put("is_rate", isRate)
            put("is_discrete", isDiscrete)
            put("is_kpi", isKpi)
            put("is_impact", isImpact)
            put("is_key_attribute", isKeyAttribute)
            put("dashboard_order", dashboardOrder)
            put("data_type", dataType)
            put("is_property", isProperty)
        }
}

/**
 * @param key Used to identify the parameter.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param unit Specifies what unit this metric is returned in. This allows the UI to display the units in a
 * consistent manner, and perform conversions when appropriate.
 * @param isRate Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
 * will be set automatically. Otherwise, defaults to False.
 * @param isDiscrete Declares that this attribute's range of values is discrete (integer) rather than continuous
 * (floating point). Defaults to False, unless 'is_string' is set, in which case it will always be set to True.
 * @param isKpi If set, threshold breaches for this metric will be used in the calculation of the object's
 * 'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
 * @param isImpact If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
 * proxy to a root cause, but not the root cause itself.
 * @param isKeyAttribute True if the attribute should be shown in some object summary widgets in the UI.
 * @param dashboardOrder Determines the order parameters will be displayed in the UI.
 */
class MetricAttribute @JvmOverloads constructor(
    key: String,
    label: String = key,
    unit: SdkUnit = Units.None,
    isRate: Boolean = unit.isRate,
    isDiscrete: Boolean = false,
    isKpi: Boolean = false,
    isImpact: Boolean = false,
    isKeyAttribute: Boolean = false,
    dashboardOrder: Int = 0,
) : Attribute(
    key,
    label,
    unit,
    isRate,
    isDiscrete,
    isKpi,
    isImpact,
    isKeyAttribute,
    dashboardOrder
) {
    override val dataType: String = if (isDiscrete) {
        "integer"
    } else {
        "float"
    }
    override val isProperty: Boolean = false
}

/**
 * @property key Used to identify the parameter.
 * @property label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @property unit Specifies what unit this metric is returned in. This allows the UI to display the units in a
 * consistent manner, and perform conversions when appropriate.
 * @property isRate Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
 * will be set automatically. Otherwise, defaults to False.
 * @property isDiscrete Declares that this attribute's range of values is discrete (integer) rather than continuous
 * (floating point). Defaults to False, unless 'is_string' is set, in which case it will always be set to True.
 * @property isKpi If set, threshold breaches for this metric will be used in the calculation of the object's
 * 'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
 * @property isImpact If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
 * proxy to a root cause, but not the root cause itself.
 * @property isKeyAttribute True if the attribute should be shown in some object summary widgets in the UI.
 */
class MetricAttributeBuilder(val key: String) {
    var label: String = key
    var unit: SdkUnit = Units.None
    var isRate: Boolean = unit.isRate
    var isDiscrete: Boolean = false
    var isKpi: Boolean = false
    var isImpact: Boolean = false
    var isKeyAttribute: Boolean = false
    fun build(dashboardOrder: Int) = MetricAttribute(key, label, unit, isRate, isDiscrete, isKpi, isImpact, isKeyAttribute, dashboardOrder)
}

/**
 * @param key Used to identify the parameter.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param isString Determines if the property is numeric or string (text).
 * @param unit Specifies what unit this metric is returned in. This allows the UI to display the units in a
 * consistent manner, and perform conversions when appropriate.
 * @param isRate Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
 * will be set automatically. Otherwise, defaults to False.
 * @param isDiscrete Declares that this attribute's range of values is discrete (integer) rather than continuous
 * (floating point). Defaults to False, unless [isString] is set, in which case it will always be set to True.
 * @param isKpi If set, threshold breaches for this metric will be used in the calculation of the object's
 * 'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
 * @param isImpact If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
 * proxy to a root cause, but not the root cause itself.
 * @param isKeyAttribute True if the attribute should be shown in some object summary widgets in the UI.
 * @param dashboardOrder Determines the order parameters will be displayed in the UI.
 */
class PropertyAttribute @JvmOverloads constructor(
    key: String,
    label: String = key,
    isString: Boolean = true,
    unit: SdkUnit = Units.None,
    isRate: Boolean = unit.isRate,
    isDiscrete: Boolean = false,
    isKpi: Boolean = false,
    isImpact: Boolean = false,
    isKeyAttribute: Boolean = false,
    dashboardOrder: Int = 0,
) : Attribute(
    key,
    label,
    unit,
    isRate,
    isString or isDiscrete,
    isKpi,
    isImpact,
    isKeyAttribute,
    dashboardOrder
) {
    override val dataType: String = if (isString) {
        "string"
    } else if (isDiscrete) {
        "integer"
    } else {
        "float"
    }
    override val isProperty: Boolean = true
}

/**
 * @property key Used to identify the parameter.
 * @property label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @property isKpi If set, threshold breaches for this metric will be used in the calculation of the object's
 * 'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
 * @property isImpact If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
 * proxy to a root cause, but not the root cause itself.
 * @property isKeyAttribute True if the attribute should be shown in some object summary widgets in the UI.
 */
class StringPropertyAttributeBuilder(val key: String) {
    var label: String = key
    var isKpi: Boolean = false
    var isImpact: Boolean = false
    var isKeyAttribute: Boolean = false
    fun build(dashboardOrder: Int) = PropertyAttribute(key, label, true, Units.None, false, true, isKpi, isImpact, isKeyAttribute, dashboardOrder)
}

/**
 * @property key Used to identify the parameter.
 * @property label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @property unit Specifies what unit this metric is returned in. This allows the UI to display the units in a
 * consistent manner, and perform conversions when appropriate.
 * @property isRate Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
 * will be set automatically. Otherwise, defaults to False.
 * @property isDiscrete Declares that this attribute's range of values is discrete (integer) rather than continuous
 * (floating point). Defaults to False.
 * @property isKpi If set, threshold breaches for this metric will be used in the calculation of the object's
 * 'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
 * @property isImpact If set, this attribute will never be the 'root cause' of an issue. For example, it could be a
 * proxy to a root cause, but not the root cause itself.
 * @property isKeyAttribute True if the attribute should be shown in some object summary widgets in the UI.
 */
class NumericPropertyAttributeBuilder(val key: String) {
    var label: String = key
    var unit: SdkUnit = Units.None
    var isRate: Boolean = unit.isRate
    var isDiscrete: Boolean = false
    var isKpi: Boolean = false
    var isImpact: Boolean = false
    var isKeyAttribute: Boolean = false
    fun build(dashboardOrder: Int) = PropertyAttribute(key, label, false, unit, isRate, isDiscrete, isKpi, isImpact, isKeyAttribute, dashboardOrder)
}
