/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Metric private constructor(
    val key: String,
    @SerialName("numberValue") val doubleValue: Double,
    val timestamp: Long = System.currentTimeMillis(),
) {
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
     * @property key A string identifying the metric.
     * @property numberValue The value of the metric. Note: VMware Aria Operations treats
     * all numeric values as a [Double].
     * @property timestamp Time in milliseconds since the Epoch when this metric value was
     * recorded. Defaults to the current time.
     */
    @JvmOverloads
    constructor(
        key: String,
        numberValue: Number,
        timestamp: Long = System.currentTimeMillis(),
    ) : this(key, numberValue.toDouble(), timestamp)
}

@Serializable
sealed class Property {
    abstract val key: String
    abstract val timestamp: Long
}

/**
 * Class representing a String Property value.
 *
 * A String Property is a value that will change infrequently or not at all.
 *
 * Examples:
 *     IP Address
 *     Software Version
 *
 * @property key A string identifying the property.
 * @property stringValue The value of the property.
 * @property timestamp Time in milliseconds since the Epoch when this property value was
 * recorded. Defaults to the current time.
 */
@Serializable
data class StringProperty @JvmOverloads constructor(
    override val key: String,
    val stringValue: String,
    override val timestamp: Long = System.currentTimeMillis(),
) : Property()

@Serializable
data class NumericProperty private constructor(
    override val key: String,
    @SerialName("numberValue") val doubleValue: Double,
    override val timestamp: Long = System.currentTimeMillis(),
) : Property() {
    /**
     * Class representing a Numeric Property value.
     *
     * A Numeric Property is a value that will change infrequently or not at all.
     *
     * Examples:
     *     CPU Core Count
     *     Replication Nodes
     *
     * @property key A string identifying the property.
     * @property numberValue The value of the metric. Note: VMware Aria Operations treats
     * all numeric values as a [Double].
     * @property timestamp Time in milliseconds since the Epoch when this metric value was
     * recorded. Defaults to the current time.
     */
    @JvmOverloads
    constructor(
        key: String,
        numberValue: Number,
        timestamp: Long = System.currentTimeMillis(),
    ) : this(key, numberValue.toDouble(), timestamp)
}

