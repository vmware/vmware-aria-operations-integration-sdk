/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
@file:JvmName("Result")

package com.vmware.aria.operations

import com.vmware.aria.operations.definition.AdapterDefinition
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.encodeToJsonElement

enum class RelationshipUpdateModes {
    /**
     * If [CollectResult.updateRelationships] is [ALL], all relationships between objects are
     * returned. This mode will remove any currently-existing relationships in VMware
     * Aria Operations that are not present in the Result.
     */
    ALL,

    /**
     * If [CollectResult.updateRelationships] is [NONE], no relationships will be returned, even if
     * there are relationships between objects in the Result. All currently-existing
     * relationships in VMware Aria Operations will be preserved.
     */
    NONE,

    /**
     * If [CollectResult.updateRelationships] is [AUTO] (or not explicitly set), then the mode will
     * behave like 'ALL' if any object in the Result has at least one relationship,
     * otherwise the mode will behave like 'NONE' if no objects have any relationships in
     * the Result. This default behavior makes it easy to skip collecting all relationships
     * for a collection without overwriting previously-collected relationships, e.g., for
     * performance reasons.
     */
    AUTO,

    /**
     * If [CollectResult.updateRelationships] is [PER_OBJECT], then only objects with updated
     * relationships will be returned. This is similar to 'AUTO' except that if an
     * object's child relationships have not been updated/set (by calling 'add_child' or
     * 'add_children'), existing child relationships in VMware Aria Operations will be
     * preserved. This means that to remove all relationships from an [Object]
     * (without setting any new relationships), the adapter must call [Object.addChildren] on
     * the object with an empty collection of children. This mode is useful for updating a
     * subset of objects' relationships in a collection, but requires more care to
     * ensure relationships are removed when appropriate.
     */
    PER_OBJECT,
}

/**
 * Class for managing the results of an Adapter Instance 'connection' test
 */
@Serializable
class TestResult {
    private var errorMessage: String? = null

    /**
     * @return true if the TestResult represents a successful test
     */
    fun isSuccess() = errorMessage == null

    /**
     * Set the adapter instance connection test to failed, and display the given
     * error message.
     *
     * If this method is called multiple times, only the most recent error message
     * will be recorded. If [errorMessage] is set, the test is considered failed.
     *
     * @param errorMessage The error message to present to the user.
     */
    fun withError(errorMessage: String) = apply {
        this.errorMessage = errorMessage
    }

    /**
     * @return Returns a JSON representation of this [TestResult] in the format required by
     * Aria Operations, indicating either a successful test, or a failed test with
     * error message.
     */
    val json: JsonElement
        get() = Json.encodeToJsonElement(this)

    /**
     * Opens the output pipe and sends result directly back to the server
     *
     * This method can only be called once per collection.
     *
     * @param outputPipe The path to the output pipe.
     */
    @JvmOverloads
    fun sendResults(outputPipe: String = Pipes.output) {
        writeToPipe(json, outputPipe)
    }
}

/**
 * Class for managing the results of an adapter's getEndpointURLs call
 *
 * The result of is a set of urls that the adapter will connect to.
 * Aria Operations will then attempt to connect to each of these urls securely,
 * and prompt the user to accept or reject the certificate presented by each URL.
 */
@Serializable
class EndpointResult {
    private val endpointUrls = mutableSetOf<String>()

    /**
     * Adds an endpoint to the set of endpoints Aria Operations will test for
     * certificate validation.
     *
     * If this method is called multiple times, each url will be called by Aria
     * Operations.
     *
     * @param endpoint A string containing the url
     */
    fun withEndpoint(endpoint: String) = apply {
        this.endpointUrls.add(endpoint)
    }

    /**
     * @return Returns a JSON representation of this [EndpointResult] in the format required by
     * Aria Operations.
     */
    val json: JsonElement
        get() = Json.encodeToJsonElement(this)

    /**
     * Opens the output pipe and sends results directly back to the server
     * This method can only be called once per collection.
     * @param outputPipe The path to the output pipe.
     */
    @JvmOverloads
    fun sendResults(outputPipe: String = Pipes.output) {
        writeToPipe(json, outputPipe)
    }
}

/**
 * Class for managing the results of an adapter's collection call.
 *
 * A [CollectResult] contains [Objects][Object], which can be added at initialization or later.
 * Each [Object] has a [Key] containing one or more [Identifiers][Identifier] plus the object type
 * and adapter type. [Keys][Key] must be unique across objects in a [CollectResult].
 *
 * @param objectList An optional [List] of objects to send to Aria Operations. [Objects][Object] can be
 * added later using [CollectResult.addObject]. Defaults to an empty list.
 * @param targetDefinition an optional description of the returned objects, used for validation
 * purposes. Defaults to null.
 */
class CollectResult(
    objectList: List<Object> = emptyList(),
    private val targetDefinition: AdapterDefinition? = null,
) {
    private val objects = mutableMapOf<Key, Object>()
    private val adapterType: String?
    private var errorMessage: String? = null
    var updateRelationships = RelationshipUpdateModes.AUTO

    init {
        addObjects(objectList)
        adapterType = targetDefinition?.adapterType
    }

    fun isSuccess() = errorMessage == null

    /**
     * Set the Adapter Instance to an error state with the provided message.
     *
     * If this method is called multiple times, only the most recent error message
     * will be recorded. If [errorMessage] is set, no other [Objects][Object] (including the
     * object's [Events][Event], [Properties][Property], [Metrics][Metric], and Relationships)
     * will be returned in the [CollectResult].
     *
     * @param errorMessage A string containing the error message
     */
    fun withError(errorMessage: String) = apply {
        this.errorMessage = errorMessage
    }

    /**
     * An object is external if it was created by a different adapter than this one.
     *
     * @param obj [Object] to test if it is external.
     * @return true if the [Object Type][Object.objectType] of [obj] does not match the object type set by
     * [targetDefinition]. If [targetDefinition] has not been set, this always returns false.
     */
    private fun objectIsExternal(obj: Object) =
        adapterType != null && adapterType != obj.adapterType

    /**
     * Get or create the [Object] with the [Key] given by the provided identification
     * ([adapterType], [objectType], name, and identifiers).
     *
     * This is the preferred method for creating new Objects. If this method is used
     * exclusively, all [Object] references with the same key will point to the same
     * object.
     *
     * If an [Object] with the same key already exists in the [CollectResult], return that
     * [Object], otherwise create a new [Object], add it to the [CollectResult], and return it.
     * See discussion on keys in the documentation for the [Key] class.
     *
     * If this method is used to create an [Object], it does not need to be added
     * later using [addObject] or [addObjects].
     *
     * @param adapterType The adapter type of the object
     * @param objectType The type of the object
     * @param name The name of the object
     * @param identifiers An optional list of [Identifiers][Identifier] for the object
     *
     * @return The [Object] with the given [Key]
     */

    @JvmOverloads
    fun getOrCreateObject(
        adapterType: String,
        objectType: String,
        name: String,
        identifiers: List<Identifier> = emptyList(),
    ): Object {
        val key = Key(adapterType, objectType, name, identifiers)
        return getOrCreateObject(key)
    }

    /**
     * Get or create the object with key specified by the [key].
     *
     * This is the preferred method for creating new Objects. If this method is used
     * exclusively, all [Object] references with the same key will point to the same
     * object.
     *
     * If an [Object] with the same key already exists in the [CollectResult], return that
     * [Object], otherwise create a new [Object], add it to the [CollectResult], and return it.
     * See discussion on keys in the documentation for the [Key] class.
     *
     * If this method is used to create an [Object], it does not need to be added
     * later using [addObject] or [addObjects].
     *
     * @param key The [Key] that identifies the object
     * @return The [Object] with the given [Key]
     */
    fun getOrCreateObject(
        key: Key,
    ): Object {
        val obj = Object(key)
        return objects.getOrPut(obj.key) { obj }
    }

    /**
     * Get and return the [Object] corresponding to the given identification, if it exists.
     *
     * @param adapterType The adapter type of the object
     * @param objectType The type of the object
     * @param name The name of the object
     * @param identifiers An optional list of [Identifiers][Identifier] for the object
     * @return The [Object] with the given [Key], or null if an [Object] with the given
     * [Key] is not in the [CollectResult]
     */
    @JvmOverloads
    fun getObject(
        adapterType: String,
        objectType: String,
        name: String,
        identifiers: List<Identifier> = emptyList(),
    ): Object? {
        val key = Key(adapterType, objectType, name, identifiers)
        return getObject(key)
    }

    /**
     * Get and return the [Object] corresponding to the given [Key], if it exists.
     *
     * @param key The object key to search for
     * @return The [Object] with the given [Key], or null if an [Object] with the given
     * [Key] is not in the [CollectResult]
     */
    fun getObject(
        key: Key,
    ): Object? {
        return objects[key]
    }

    /**
     * Returns all [Objects][Object] in this [CollectResult].
     * @return The [List] of [Objects][Object]
     */
    fun getObjects(): List<Object> = objects.values.toList()

    /**
     * Returns all [Objects][Object] with the given type.
     * @param objectType The [object type][Key.objectType] to match
     * @return A [List] of [Objects][Object] matching the [objectType]
     */
    fun getObjectsByType(objectType: String) =
        objects.values.filter { obj ->
            obj.objectType == objectType
        }

    /**
     * Returns all [Objects][Object] with the given adapter type and object type.
     * @param adapterType The [adapter type][Key.adapterType] to match
     * @param objectType The [object type][Key.objectType] to match
     * @return A [List] of [Objects][Object] matching the [adapterType] and [objectType]
     */
    fun getObjectsByType(adapterType: String, objectType: String) =
        objects.values.filter { obj ->
            obj.adapterType == adapterType && obj.objectType == objectType
        }

    /**
     * Returns all [Objects][Object] with the given adapter type.
     * @param adapterType The [adapter type][Key.adapterType] to match
     * @return A [List] of [Objects][Object] matching the [adapterType] and [objectType]
     */
    fun getObjectsByAdapterType(adapterType: String) =
        objects.values.filter { obj ->
            obj.adapterType == adapterType
        }

    /**
     * Adds the given [Object] to the [CollectResult] and returns it.
     *
     * A different [Object] with the same key cannot already exist in the [CollectResult].
     * If it does, an [ObjectKeyAlreadyExistsException] will be thrown.
     *
     * @param obj The [Object] to add to the [CollectResult].
     * @return The object.
     * @throws ObjectKeyAlreadyExistsException: If a different [Object] with the same [Key]
     * already exists in the [CollectResult].
     */
    fun addObject(obj: Object): Object {
        val o = objects.getOrPut(obj.key) { obj }
        if (o === obj)
            return o
        throw ObjectKeyAlreadyExistsException(obj.key)
    }

    /**
     * Adds the given [Objects][Object] to the [CollectResult].
     *
     * A different [Object] with the same key cannot already exist in the [CollectResult].
     * If it does, an [ObjectKeyAlreadyExistsException] will be thrown. All [Objects][Object]
     * will attempt to add to the [CollectResult].
     *
     * @param objects A [Collection] of [Objects][Object] to add to the [CollectResult].
     * @throws ObjectKeyAlreadyExistsException: If any [Objects][Object] with the same [Key]
     * already exists in the [CollectResult].
     */
    fun addObjects(objects: Iterable<Object>) {
        val failed = mutableListOf<Key>()
        for (obj in objects) {
            try {
                addObject(obj)
            } catch (_: ObjectKeyAlreadyExistsException) {
                failed.add(obj.key)
            }
        }
        if (failed.isNotEmpty()) {
            throw ObjectKeyAlreadyExistsException(failed)
        }
    }

    /**
     * @return a JSON representation of this [CollectResult] in the format required by Aria
     * Operations. The representation includes all *internal* [Objects][Object] (including the object's
     * [Events][Event], [Properties][Property], and [Metrics][Metric]) in the [CollectResult], plus
     * any *external* [Objects][Object] that have added content.
     * Relationships are returned following the [updateRelationships] flag
     * (See [RelationshipUpdateModes]).
     *
     */
    val json: JsonObject
        get() {
            val result = mutableMapOf<String, JsonElement>()
            if (errorMessage != null) {
                result["errorMessage"] = JsonPrimitive(errorMessage)
            } else {
                val relationshipUpdates: Collection<Object> =
                    when (updateRelationships) {
                        RelationshipUpdateModes.NONE -> emptyList()
                        RelationshipUpdateModes.ALL -> objects.values
                        RelationshipUpdateModes.PER_OBJECT -> objects.values.filter { it.hasUpdatedChildren }
                        RelationshipUpdateModes.AUTO -> if (objects.values.any { it.hasUpdatedChildren }) objects.values else emptyList()
                    }
                result["result"] =
                    Json.encodeToJsonElement(objects.values
                        .filter { obj -> !objectIsExternal(obj) or obj.hasContent() }
                        .map{ obj -> obj.json})
                result["relationships"] =
                    Json.encodeToJsonElement(relationshipUpdates.map { obj ->
                        mapOf(
                            "parent" to Json.encodeToJsonElement(obj.key),
                            "children" to Json.encodeToJsonElement(obj.getChildren())
                        )
                    })
                result["nonExistingObjects"] = JsonArray(listOf())
            }
            return JsonObject(result)
        }

    /**
     * Opens the output pipe and sends results directly back to the server
     * This method can only be called once per collection.
     * @param outputPipe The path to the output pipe.
     */
    @JvmOverloads
    fun sendResults(outputPipe: String = Pipes.output) {
        writeToPipe(json, outputPipe)
    }
}
