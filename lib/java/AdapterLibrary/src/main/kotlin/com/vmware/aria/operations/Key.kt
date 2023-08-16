/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

/**
 * Initializes a Key, which uniquely identifies a VMware Aria Operations [Object].
 *
 * @param adapterType The Adapter Type this Object is associated with.
 * @param objectType The Object Type (e.g., class) of this Object.
 * @param name A human-readable name for this Object. Should be unique if possible.
 * @param identifiers A list of [Identifier]s that uniquely identify the Object. If none are present than
 * the name must be unique and is used for identification. All Objects with the same adapter type and Object
 * type must have the same set of identifiers.
 */
class Key @JvmOverloads constructor(
    adapterType: String,
    objectType: String,
    name: String,
    identifiers: List<Identifier> = emptyList()
) {
    /**
     * Object's Key class, used for identifying [Object]s
     *
     * Objects are identified by the Adapter Type, Object Type, and one or more Identifiers.
     *
     * Identifiers can be either the Object's 'name', or one or more [Identifier] key-value pairs.
     * In order for an 'Identifier' to be used for identification, it must have
     * [Identifier.isPartOfUniqueness] set to true (this is the default).
     *
     * Two Objects with the same Key are not permitted in a [CollectResult].
     *
     * Objects must be created with the full key. Keys should not change after the Object has been created.
     *
     * All Objects with the same Adapter Type and Object Type must have the same set of Identifiers that have
     * 'isPartOfUniqueness' set to true.
     */
    val adapterType: String
    val objectType: String
    val name: String
    private val identifiers: Map<String, Identifier>

    init {
        this.adapterType = adapterType
        this.objectType = objectType
        this.name = name
        this.identifiers = HashMap()
        for (identifier in identifiers) {
            this.identifiers[identifier.key] = identifier
        }
    }

    override fun toString(): String {
        return "$adapterType:$objectType:$identifiers"
    }

    /**
     * Return a list of data and identifiers that determine uniqueness
     */
    private val internalKey: List<Any>
        get() {
            // Sort all identifiers by 'key' that are part of uniqueness
            val uniqueIdentifiers =
                identifiers.values.filter { identifier -> identifier.isPartOfUniqueness }
            val key = mutableListOf<Any>()
            key.add(adapterType)
            key.add(objectType)
            if (uniqueIdentifiers.isEmpty()) {
                //If there are no identifiers, or if all identifiers are not part of
                // uniqueness, the name is used as uniquely identifying
                key.add(name)
            } else {
                // Otherwise,if there is at least one identifier that is part of
                // uniqueness, name is not used for
                // identification. Add each of the unique identifiers to the list, sorted
                // by key
                key.addAll(uniqueIdentifiers.sortedBy { identifier -> identifier.key })
            }
            return key
        }

    /**
     * @return True if the keys will resolve to the same object, false otherwise.
     */
    override fun equals(other: Any?): Boolean {
        return if (other is Key) {
            internalKey == other.internalKey
        } else {
            false
        }
    }

    /**
     * Return a hashcode of this Key, respecting the rules of key uniqueness
     */
    override fun hashCode(): Int =
        internalKey.fold(0) { acc, id -> acc xor id.hashCode() }

    /**
     * Return the value for the given identifier key.
     * @param key The identifier key.
     * @param defaultValue An optional default value.
     * @return The value associated with the identifier.
     * If the value associated with the identifier is empty and 'defaultValue' is
     * provided, returns 'defaultValue'.
     * If the identifier does not exist, returns defaultValue if provided, else 'null'.
    */
    @JvmOverloads
    fun getIdentifier(key: String, defaultValue: String? = null): String? {
        val value = identifiers[key]?.value
        return if (value?.isBlank() != false) {
            defaultValue ?: value
        } else {
            value
        }
    }

    /**
     * Get a JSON representation of this Key.
     * This method returns a JSON representation of this Key in the format required by VMware Aria Operations.
     * @return The JSON representation of this Key, as a Map
     */
    val json: Map<String, Any>
        get() =
            mapOf(
                "name" to name,
                "adapterKind" to adapterType,
                "objectKind" to objectType,
                "identifiers" to identifiers.map { (_, identifier) -> identifier.json }
            )
}
