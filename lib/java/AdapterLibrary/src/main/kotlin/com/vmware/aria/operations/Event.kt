/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

import kotlinx.serialization.Serializable

/**
 * Enum representing the different severities an event in VMware Aria Operations can have
 */
enum class Criticality(val id: Int) {
    NONE(0),
    INFO(1),
    WARNING(2),
    IMMEDIATE(3),
    CRITICAL(4),
    AUTOMATIC(5),
}

@Serializable
data class Event private constructor(
    val message: String,
    val criticality: Int = Criticality.NONE.id,
    val faultKey: String? = null,
    val autoCancel: Boolean = true,
    val startDate: Long? = null,
    val updateDate: Long? = null,
    val cancelDate: Long? = null,
    val watchWaitCycle: Int = 1,
    val cancelWaitCycle: Int = 3,
) {
    /**
     * Represents a VMware Aria Operations Event
     *
     * @property message The message describes and identifies an event.
     * @property criticality The criticality or severity of the event.
     * @property faultKey A metric/property key that this event is related to. Defaults to null, which
     *  indicates the event's source is not related to a metric or property.
     * @property autoCancel If True, VMware Aria Operations should automatically cancel an event
     * when it stops being sent. Otherwise, it is the responsibility of the adapter
     * to send the event with a 'cancel_date' when the event should be canceled.
     * Defaults to True.
     * @property startDate If set, overrides the start date of the event. Defaults to null, which indicates
     *  the start time should be the time when VMware Aria Operations first sees the event.
     * @property updateDate If set, indicates that the event has been updated by the target at the
     *  indicated time. Defaults to null.
     * @property cancelDate If 'autoCancel' is set to False, use the cancelDate to indicate that the event should
     *  be cancelled. Defaults to null.
     * @property watchWaitCycle The number of times this event must be present in a collection before VMware Aria
     *  Operations surfaces it in the UI. Defaults to 1.
     * @property cancelWaitCycle If 'autoCancel' is set to true, sets the number of times this event must be
     *  absent in a collection before Aria Operations removes it from the UI. Defaults to 3.
     */
    @JvmOverloads constructor(
        message: String,
        criticality: Criticality = Criticality.NONE,
        faultKey: String? = null,
        autoCancel: Boolean = true,
        startDate: Long? = null,
        updateDate: Long? = null,
        cancelDate: Long? = null,
        watchWaitCycle: Int = 1,
        cancelWaitCycle: Int = 3,
    ) : this(
        message,
        criticality.id,
        faultKey,
        autoCancel,
        startDate,
        updateDate,
        cancelDate,
        watchWaitCycle,
        cancelWaitCycle,
    )
}

