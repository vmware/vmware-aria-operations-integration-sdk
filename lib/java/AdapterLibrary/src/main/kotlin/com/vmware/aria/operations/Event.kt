/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

/**
 * Enum representing the different severities an event in VMware Aria Operations can have
 */
enum class Criticality {
    NONE,
    INFO,
    WARNING,
    IMMEDIATE,
    CRITICAL,
    AUTOMATIC,
}

/**
 * Represents a VMware Aria Operations Event
 *
 * @param message The message describes and identifies an event.
 * @param criticality The criticality or severity of the event.
 * @param faultKey A metric/property key that this event is related to. Defaults to null, which
 *  indicates the event's source is not related to a metric or property.
 * @param autoCancel If True, VMware Aria Operations should automatically cancel an event
 * when it stops being sent. Otherwise, it is the responsibility of the adapter
 * to send the event with a 'cancel_date' when the event should be canceled.
 * Defaults to True.
 * @param startDate If set, overrides the start date of the event. Defaults to null, which indicates
 *  the start time should be the time when VMware Aria Operations first sees the event.
 * @param updateDate If set, indicates that the event has been updated by the target at the
 *  indicated time. Defaults to null.
 * @param cancelDate If 'autoCancel' is set to False, use the cancelDate to indicate that the event should
 *  be cancelled. Defaults to null.
 * @param watchWaitCycle The number of times this event must be present in a collection before VMware Aria
 *  Operations surfaces it in the UI. Defaults to 1.
 * @param cancelWaitCycle If 'autoCancel' is set to true, sets the number of times this event must be
 *  absent in a collection before Aria Operations removes it from the UI. Defaults to 3.
 */
class Event @JvmOverloads constructor(
    val message: String,
    val criticality: Criticality = Criticality.NONE,
    val faultKey: String? = null,
    val autoCancel: Boolean = true,
    val startDate: Long? = null,
    val updateDate: Long? = null,
    val cancelDate: Long? = null,
    val watchWaitCycle: Int = 1,
    val cancelWaitCycle: Int = 3,
) {
    val json: Map<String, Any>
        get() = mutableMapOf(
            "message" to message,
            "criticality" to criticality,
            "autoCancel" to autoCancel,
            "watchWaitCycle" to watchWaitCycle,
            "cancelWaitCycle" to cancelWaitCycle
        ).apply {
            if (faultKey != null) {
                put("faultKey", faultKey)
            }
            if (startDate != null) {
                put("startDate", startDate)
            }
            if (updateDate != null) {
                put("updateDate", updateDate)
            }
            if (cancelDate != null) {
                put("cancelDate", cancelDate)
            }
        }
}
