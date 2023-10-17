/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations.definition

import com.vmware.aria.operations.DuplicateKeyException
import com.vmware.aria.operations.KeyException
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray
import java.util.function.Consumer

abstract class GroupType @Throws(KeyException::class) constructor() {
    abstract val key: String
    private val attributeMap = LinkedHashMap<String, Attribute>()
    private val groupMap = LinkedHashMap<String, Group>()

    /**
     * Create a new group that can hold attributes and subgroups.
     *
     * @param key The key for the group.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     *
     * @return The created group.
     */
    @Throws(DuplicateKeyException::class)
    @JvmOverloads
    fun defineGroup(key: String, label: String = key): Group {
        val group = Group(key, label)
        addGroup(group)
        return group
    }

    /**
     * Create a new group that can hold attributes and subgroups. This group can be 'instanced', with a value, so that
     * its subgroups and attributes can appear multiple times, once for each instance value. For example, a group
     * containing metrics for a network interface might be instanced for each discovered interface on the parent
     * object.
     *
     * @param key The key for the group.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param instanceRequired If true, then this group must be created with an instance. Otherwise, it can be
     * created both with and without an instance. Creating an instanced group without an instance can be done
     * to provide a location for aggregate metrics across all instances, for example.
     * @return The created group.
     */
    @Throws(DuplicateKeyException::class)
    @JvmOverloads
    fun defineInstancedGroup(
        key: String,
        label: String = key,
        instanceRequired: Boolean = true,
    ): Group {
        val group = Group(key, label, true, instanceRequired)
        addGroup(group)
        return group
    }

    /**
     * Adds a list of groups as subgroups of this group.
     *
     * @param groups A list of groups.
     */
    @Throws(DuplicateKeyException::class)
    fun addGroups(groups: Iterable<Group>) {
        groups.forEach { group ->
            addGroup(group)
        }
    }

    /**
     * Adds a group as a subgroup of this group.
     *
     * @param group A group.
     */
    @Throws(DuplicateKeyException::class)
    fun addGroup(group: Group) {
        val key = group.key
        if (this.groupMap.containsKey(key)) {
            throw DuplicateKeyException("Group with key $key already exists in ${this.javaClass.superclass} ${this.key}.")
        }
        this.groupMap[key] = group
    }

    /**
     * @param key Used to identify the parameter.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param unit Specifies what unit this metric is returned in. This allows the UI to display the
     * units in a consistent manner, and perform conversions when appropriate.
     * @param isRate Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, this
     * will be set automatically. Otherwise, defaults to False.
     * @param isDiscrete Declares that this attribute's range of values is discrete (integer) rather than
     * continuous (floating point)
     * @param isKpi If set, threshold breaches for this metric will be used in the calculation of the object's
     * 'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
     * @param isImpact If set, this attribute will never be the 'root cause' of an issue. For example, it could
     * be a proxy to a root cause, but not the root cause itself.
     * @param isKeyAttribute True if the attribute should be shown in some object summary widgets in the UI.
     */
    @Throws(DuplicateKeyException::class)
    @JvmOverloads
    fun defineMetric(
        key: String,
        label: String = key,
        unit: SdkUnit = Units.None,
        isRate: Boolean = unit.isRate,
        isDiscrete: Boolean = false,
        isKpi: Boolean = false,
        isImpact: Boolean = false,
        isKeyAttribute: Boolean = false,
    ): MetricAttribute {
        val metric = MetricAttribute(
            key,
            label,
            unit,
            isRate,
            isDiscrete,
            isKpi,
            isImpact,
            isKeyAttribute,
            dashboardOrder = this.attributeMap.size,
        )
        addAttribute(metric)
        return metric
    }

    /**
     * Create a new metric definition and add it to the containing object definition.
     * @param key Used to identify the metric.
     * @param block Anonymous function taking a [MetricAttributeBuilder] as a parameter that can be used to override
     * default values of the attribute. This is particularly useful in Java.
     */
    fun defineMetric(key: String, block: Consumer<MetricAttributeBuilder>): MetricAttribute {
        val metricBuilder = MetricAttributeBuilder(key)
        block.accept(metricBuilder)
        val metric = metricBuilder.build(this.attributeMap.size)
        addAttribute(metric)
        return metric
    }

    /**
     * @param key Used to identify the parameter.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param isKpi If set, threshold breaches for this metric will be used in the calculation of the object's
     * 'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
     * @param isImpact If set, this attribute will never be the 'root cause' of an issue. For example, it could
     * be a proxy to a root cause, but not the root cause itself.
     * @param isKeyAttribute True if the attribute should be shown in some object summary widgets in the UI.
     */
    @Throws(DuplicateKeyException::class)
    @JvmOverloads
    fun defineStringProperty(
        key: String,
        label: String = key,
        isKpi: Boolean = false,
        isImpact: Boolean = false,
        isKeyAttribute: Boolean = false,
    ): PropertyAttribute {
        val property = PropertyAttribute(
            key,
            label,
            true,
            Units.None,
            false,
            true,
            isKpi,
            isImpact,
            isKeyAttribute,
            dashboardOrder = this.attributeMap.size,
        )
        addAttribute(property)
        return property
    }

    /**
     * Create a new string property definition and add it to the containing object definition.
     * @param key Used to identify the property
     * @param block Anonymous function taking a [StringPropertyAttributeBuilder] as a parameter that can be used to override
     * default values of the attribute. This is particularly useful in Java.
     */
    fun defineStringProperty(key: String, block: Consumer<StringPropertyAttributeBuilder>): PropertyAttribute {
        val propertyBuilder = StringPropertyAttributeBuilder(key)
        block.accept(propertyBuilder)
        val property = propertyBuilder.build(this.attributeMap.size)
        addAttribute(property)
        return property
    }

    /**
     * @param key Used to identify the parameter.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param unit Specifies what unit this metric is returned in. This allows the UI to display the
     * units in a consistent manner, and perform conversions when appropriate.
     * @param isRate Declares this attribute as a rate (e.g., kilobytes per second). If a unit is specified, the
     * default will be set automatically. Otherwise, defaults to False.
     * @param isDiscrete Declares that this attribute's range of values is discrete (integer) rather than
     * continuous (floating point). Defaults to False.
     * @param isKpi If set, threshold breaches for this metric will be used in the calculation of the object's
     * 'Self - Health Score' metric, which can affect the 'Anomalies' Badge.
     * @param isImpact If set, this attribute will never be the 'root cause' of an issue. For example, it could
     * be a proxy to a root cause, but not the root cause itself.
     * @param isKeyAttribute True if the attribute should be shown in some object summary widgets in the UI.
     */
    @Throws(DuplicateKeyException::class)
    @JvmOverloads
    fun defineNumericProperty(
        key: String,
        label: String = key,
        unit: SdkUnit = Units.None,
        isRate: Boolean = unit.isRate,
        isDiscrete: Boolean = false,
        isKpi: Boolean = false,
        isImpact: Boolean = false,
        isKeyAttribute: Boolean = false,
    ): PropertyAttribute {
        val property = PropertyAttribute(
            key,
            label,
            false,
            unit,
            isRate,
            isDiscrete,
            isKpi,
            isImpact,
            isKeyAttribute,
            dashboardOrder = this.attributeMap.size,
        )
        addAttribute(property)
        return property
    }


    /**
     * Create a new numeric property definition and add it to the containing object definition.
     * @param key Used to identify the property
     * @param block Anonymous function taking a [StringPropertyAttributeBuilder] as a parameter that can be used to override
     * default values of the attribute. This is particularly useful in Java.
     */
    @Throws(DuplicateKeyException::class)
    fun defineNumericProperty(key: String, block: Consumer<NumericPropertyAttributeBuilder>): PropertyAttribute {
        val propertyBuilder = NumericPropertyAttributeBuilder(key)
        block.accept(propertyBuilder)
        val property = propertyBuilder.build(this.attributeMap.size)
        addAttribute(property)
        return property
    }

    /**
     * Adds a list of attributes to this group.
     *
     * @param attributes A list of attributes (metric or property definitions).
     */
    @Throws(DuplicateKeyException::class)
    fun addAttributes(attributes: Iterable<Attribute>) {
        attributes.forEach { attribute ->
            addAttribute(attribute)
        }
    }

    /**
     * Adds an attribute to this group.
     *
     * @param attribute An attribute (metric or property definition).
     */
    @Throws(DuplicateKeyException::class)
    fun addAttribute(attribute: Attribute) {
        val key = attribute.key
        if (attributeMap.containsKey(key)) {
            throw DuplicateKeyException(
                "Attribute with key $key already exists in ${this.javaClass.superclass} ${this.key}."
            )
        }
        attributeMap[key] = attribute
    }

    open val json: JsonObject
        get() = buildJsonObject {
            putJsonArray("attributes") {
                attributeMap.values.forEach { attribute ->
                    add(attribute.json)
                }
            }
            putJsonArray("groups") {
                groupMap.values.forEach { group ->
                    add(group.json)
                }
            }
        }
}

/**
 * Create a new group that can hold attributes and subgroups.
 *
 * @param key The key for the group.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param instanced If True, this group can be 'instanced' with a value, so that its subgroups and attributes
 * can appear multiple times, once for each instance value. For example, a group containing
 * metrics for a network interface might be instanced for each discovered interface on the parent object.
 * @param instanceRequired If true, then this group must be created with an instance. Otherwise, it can be
 * created both with and without an instance. Creating an instanced group without an instance can be done
 * to provide a location for aggregate metrics across all instances, for example. This does nothing if
 * 'instanced' is False.
 */
class Group @JvmOverloads @Throws(KeyException::class) constructor(
    override val key: String,
    val label: String = key,
    val instanced: Boolean = false,
    val instanceRequired: Boolean = true,
) : GroupType() {
    init {
        if (key.isBlank()) {
            throw KeyException("Group key cannot be empty.")
        }
    }

    override val json: JsonObject
        get() = extendJsonObject(super.json) {
            put("key", key)
            put("label", label)
            put("instanced", instanced)
            put("instance_required", instanceRequired)
        }
}