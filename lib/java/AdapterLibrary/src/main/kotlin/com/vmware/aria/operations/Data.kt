/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations

/**
 * Class representing a Metric Data Point.
 * Metrics are numeric values that represent data at a particular point in time.
 * These are stored as time series data.
 *
 * Examples:
 *    CPU Utilization
 *    Disk Capacity
 *    Current User Session Count
 *    Cumulative Data Received
 *
 * @param key A string identifying metric.
 * @param value The value of the metric.
 * @param timestamp Time in milliseconds since the Epoch when this metric value was
 * recorded. Defaults to the current time.
 */
class Metric @JvmOverloads constructor(
    val key: String,
    val value: Double,
    val timestamp: Long = System.currentTimeMillis()
) {

    /**
     * This is identical to calling 'value' directly. It is included to make working
     * with metrics and properties similar.
     *
     * @return the value of the metric as a double.
     */
    val doubleValue
        get() = value
    /**
     * Get a JSON representation of this Metric.
     * This method returns a JSON representation of this Metric in the format required by VMware Aria Operations.
     * @return The JSON representation of this Metric, as a Map
     */
    val json: Map<String, Any>
        get() = mapOf(
            "key" to key,
            "numberValue" to value,
            "timestamp" to timestamp
        )
}

sealed class PropertyValueType
class StringValue(val string: String) : PropertyValueType()
class DoubleValue(val double: Double) : PropertyValueType()

/**
 * Class representing a Property value.
 *
 * A Property is a value, usually a string, that will change infrequently or not at all.
 * Only the current value is important (i.e., a graph doesn't make sense).
 *
 * Examples:
 *     IP Address
 *     Software Version
 *     CPU Core Count
 */
class Property private constructor(
    val key: String,
    val value: PropertyValueType,
    val timestamp: Long
) {
    /**
     * @param key A string identifying the property.
     * @param value The string value of the property.
     * @param timestamp Time in milliseconds since the Epoch when this property value was
     * recorded. Defaults to the current time.
     */
    constructor(
        key: String,
        value: String,
        timestamp: Long = System.currentTimeMillis()
    ) : this(key, StringValue(value), timestamp)

    /**
     * @param key A string identifying the property.
     * @param value The numeric value of the property. Note: VMware Aria Operations treats
     * all numeric values as a [Double].
     * @param timestamp Time in milliseconds since the Epoch when this property value was
     * recorded. Defaults to the current time.
     */
    constructor(
        key: String,
        value: Number,
        timestamp: Long = System.currentTimeMillis()
    ) : this(key, DoubleValue(value.toDouble()), timestamp)

    /**
     * @return the value of the property as a string. If the value is numeric, returns null.
     */
    val stringValue: String?
        get() = (value as? StringValue)?.string

    /**
     * @return the value of the property as a double. If the value is a string, returns null.
     */
    val doubleValue: Double?
        get() = (value as? DoubleValue)?.double

    /**
     * Get a JSON representation of this Property.
     * This method returns a JSON representation of this Property in the format required by VMware Aria Operations.
     * @return The JSON representation of this Property, as a Map
     */
    val json: Map<String, Any>
        get() {
            return mapOf(
                "key" to key,
                when (value) {
                    is StringValue -> "stringValue" to value.string
                    is DoubleValue -> "numberValue" to value.double
                },
                "timestamp" to timestamp,
            )
        }
}
