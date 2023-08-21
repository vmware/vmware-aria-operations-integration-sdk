/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

import kotlinx.serialization.Serializable
import kotlinx.serialization.Transient

/**
 * Represents an Object (resource) in vROps.
 *
 * Contains [Metrics][Metric], [Properties][Property], [Events][Event], and relationships
 * to other [Objects][Object]. Each [Object] is identified by a unique [Key].
 *
 * @property key A [Key] that uniquely identifies this Object.
 */
@Serializable
open class Object(val key: Key) {
    private val metrics: MutableSet<Metric> = mutableSetOf()
    private val properties: MutableSet<Property> = mutableSetOf()
    private val events: MutableSet<Event> = mutableSetOf()

    @Transient
    private val metricMap = mutableMapOf<String, MutableSet<Metric>>()

    @Transient
    private val propertyMap = mutableMapOf<String, MutableSet<Property>>()

    @Transient
    private val parents = mutableSetOf<Key>()

    @Transient
    private val children = mutableSetOf<Key>()

    @Transient
    internal var hasUpdatedChildren = false

    /**
     * @return Adapter Type of this object
     */
    val adapterType: String
        get() = key.adapterType

    /**
     * @return Object Type of this object
     */
    val objectType: String
        get() = key.objectType

    /**
     * @return The name of this object
     */
    val name: String
        get() = key.name

    /**
     * Retrieve the value of a given [Identifier].
     * @param identifierKey Key of the [Identifier]
     * @param defaultValue An optional default value
     *
     * @return The value associated with the [Identifier].
     * If the value associated with the [Identifier] is empty and [defaultValue] is
     * provided, returns [defaultValue].
     * If the [Identifier] does not exist, returns [defaultValue] if provided, else null.
     */
    @JvmOverloads
    fun getIdentifierValue(
        identifierKey: String,
        defaultValue: String? = null,
    ): String? {
        return key.getIdentifier(identifierKey, defaultValue)
    }

    /**
     * Adds a single [Metric] (data point) to this [Object]
     *
     * @param metric A [Metric] data point to add to this [Object]
     */
    fun addMetric(metric: Metric) {
        if (metrics.add(metric)) {
            metricMap.getOrPut(metric.key) { mutableSetOf() }.add(metric)
        }
    }

    /**
     * Adds a collection of [Metrics][Metric] (data points) to this [Object]
     *
     * @param metrics A collection of [Metric] data points to add to this [Object]
     */
    fun addMetrics(metrics: Iterable<Metric>) {
        for (metric in metrics) {
            addMetric(metric)
        }
    }

    /**
     * Creates a single [Metric] (data point) and adds it to this [Object]
     *
     * @param key The key identifying the [Metric]
     * @param value The value of the data point
     * @param timestamp The timestamp (in milliseconds since the Epoch) the data point
     * was collected (defaults to now).
     */
    @JvmOverloads
    fun withMetric(
        key: String,
        value: Double,
        timestamp: Long = System.currentTimeMillis(),
    ) =
        addMetric(Metric(key, value, timestamp))

    /**
     * Gets all [Metrics][Metric] for a given [Metric] key.
     *
     * @param key Metric key of the metrics to return.
     * @return A [Set] of all metrics matching the given key.
     */
    fun getMetric(key: String): Set<Metric> = metricMap.getOrDefault(key, setOf())

    /**
     * Gets all datapoints for a given [Metric] key.
     *
     * @param key Metric key of the [Metric] to return.
     * @return A [List] of the metric values matching the given key in chronological order.
     */
    fun getMetricValues(key: String): List<Double> =
        getMetric(key).sortedBy(Metric::timestamp).map(Metric::doubleValue)

    /**
     * Gets the most recent datapoint for a given [Metric] key.
     *
     * @param key Metric key of the metric to return.
     * @return The latest value of the metric, or null if no metric exists with the given key..
     */
    fun getLastMetricValue(key: String): Double? = getMetricValues(key).lastOrNull()

    /**
     * Adds a single [Property] (data point) to this [Object]
     *
     * @param property A [Property] data point to add to this [Object]
     */
    fun addProperty(property: Property) {
        if (properties.add(property)) {
            propertyMap.getOrPut(property.key) { mutableSetOf() }.add(property)
        }
    }

    /**
     * Adds a collection of [Properties][Property] (data points) to this [Object]
     *
     * @param properties A collection of [Property] data points to add to this [Object]
     */
    fun addProperties(properties: Iterable<Property>) {
        for (property in properties) {
            addProperty(property)
        }
    }

    /**
     * Creates a single [StringProperty] (data point) and adds it to this [Object]
     *
     * @param key The key identifying the [Property]
     * @param value The value of the data point
     * @param timestamp The timestamp (in milliseconds since the Epoch) the data point
     * was collected (defaults to now).
     */
    @JvmOverloads
    fun withProperty(
        key: String,
        value: String,
        timestamp: Long = System.currentTimeMillis(),
    ) =
        addProperty(StringProperty(key, value, timestamp))

    /**
     * Creates a single [NumericProperty] (data point) and adds it to this [Object]
     *
     * @param key The key identifying the [Property]
     * @param value The value of the data point
     * @param timestamp The timestamp (in milliseconds since the Epoch) the data point
     * was collected (defaults to now).
     */
    @JvmOverloads
    fun withProperty(
        key: String,
        value: Double,
        timestamp: Long = System.currentTimeMillis(),
    ) =
        addProperty(NumericProperty(key, value, timestamp))

    /**
     * Gets all [Properties][Property] for a given [Property] key.
     *
     * @param key Property key of the metrics to return.
     * @return A [Set] of all properties matching the given key.
     */
    fun getProperty(key: String): Set<Property> =
        propertyMap.getOrDefault(key, setOf())

    /**
     * Gets all datapoints for a given [NumericProperty] key.
     *
     * @param key [Property] key of the [NumericProperty] to return.
     * @return A [List] of the property values matching the given key in chronological order.
     * If the property is [StringProperty], returns an empty list.
     */
    fun getNumericPropertyValues(key: String): List<Double> =
        getProperty(key).sortedBy(Property::timestamp)
            .mapNotNull { prop -> (prop as? NumericProperty)?.doubleValue }

    /**
     * Gets all datapoints for a given [StringProperty] key.
     *
     * @param key [Property] key of the [StringProperty] to return.
     * @return A [List] of the property values matching the given key in chronological order.
     * If the property is [NumericProperty], returns an empty list.
     */
    fun getStringPropertyValues(key: String): List<String> =
        getProperty(key).sortedBy(Property::timestamp)
            .mapNotNull { prop -> (prop as? StringProperty)?.stringValue }

    /**
     * Gets the most recent datapoint for a given [NumericProperty] key.
     *
     * @param key [Property] key of the [NumericProperty] to return.
     * @return The latest value of the [NumericProperty], or null if no [NumericProperty] exists with the given key.
     */
    fun getLastNumericPropertyValue(key: String): Double? =
        getNumericPropertyValues(key).lastOrNull()

    /**
     * Gets the most recent datapoint for a given [StringProperty] key.
     *
     * @param key [Property] key of the [StringProperty] to return.
     * @return The latest value of the [StringProperty], or null if no [StringProperty] exists with the given key.
     */
    fun getLastStringPropertyValue(key: String): String? =
        getStringPropertyValues(key).lastOrNull()

    /**
     * Adds a single [Event] to this [Object].
     *
     * @param event An [Event] to add to this [Object].
     */
    fun addEvent(event: Event) {
        events.add(event)
    }

    /**
     * Adds a collection of [Events][Event] to this [Object].
     *
     * @param events The collection of [Events][Event] to add to this [Object].
     */
    fun addEvents(events: Iterable<Event>) {
        for (event in events) {
            addEvent(event)
        }
    }

    /**
     * Creates a new [Event] and adds it to this [Object].
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
    @JvmOverloads
    fun withEvent(
        message: String,
        criticality: Criticality = Criticality.NONE,
        faultKey: String? = null,
        autoCancel: Boolean = true,
        startDate: Long? = null,
        updateDate: Long? = null,
        cancelDate: Long? = null,
        watchWaitCycle: Int = 1,
        cancelWaitCycle: Int = 3,
    ) =
        addEvent(
            Event(
                message,
                criticality,
                faultKey,
                autoCancel,
                startDate,
                updateDate,
                cancelDate,
                watchWaitCycle,
                cancelWaitCycle
            )
        )

    /**
     * @return a [List] of all [Events][Event] attached to this object.
     */
    fun getEvents(): List<Event> = events.toList()

    /**
     * Adds a parent [Object] to this [Object].
     *
     * This [Object] will also be added as a child to the parent.
     *
     * Relationships cycles are not permitted.
     *
     * @param parent The parent [Object]
     */
    fun addParent(parent: Object) {
        parents.add(parent.key)
        parent.children.add(key)
    }

    /**
     * Adds a collection of parent [Objects][Object] to this [Object].
     *
     * This [Object] will also be added as a child to each of the parents.
     *
     * Relationship cycles are not permitted.
     *
     * @param parents A collection of parent [Objects][Object].
     */
    fun addParents(parents: Iterable<Object>) {
        for (parent in parents) {
            addParent(parent)
        }
    }

    /**
     * @return a [Set] of all Object [Key]s that are parents of this object.
     */
    fun getParents(): Set<Key> = parents

    /**
     * Adds a child [Object] to this [Object].
     *
     * This [Object] will also be added as a parent to the child.
     *
     * Relationships cycles are not permitted.
     *
     * @param child The parent [Object]
     */
    fun addChild(child: Object) {
        if (!children.contains(child.key)) {
            hasUpdatedChildren = true
            children.add(child.key)
            child.parents.add(key)
        }
    }

    /**
     * Adds a collection of child [Objects][Object] to this [Object].
     *
     * This [Object] will also be added as a parent to each of the children.
     *
     * Relationship cycles are not permitted.
     *
     * @param children A collection of child [Objects][Object].
     */
    fun addChildren(children: Iterable<Object>) {
        for (child in children) {
            addChild(child)
        }
    }

    /**
     * @return a [Set] of all Object [Keys][Key] that are children of this object.
     */
    fun getChildren(): Set<Key> = children

    /**
     * @return true if this [Object] contains any [Metrics][Metric], [Properties][Property],
     * or [Events][Event]; false otherwise.
     */
    fun hasContent() =
        metrics.isNotEmpty() or properties.isNotEmpty() or events.isNotEmpty()
}
