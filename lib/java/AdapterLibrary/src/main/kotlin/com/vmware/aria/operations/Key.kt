/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

import kotlinx.serialization.EncodeDefault
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.Transient

/**
 * Object's Key class, used for identifying VMware Aria Operation [Objects][Object].
 *
 * Objects are identified by the Adapter Type, Object Type, and one or more Identifiers.
 *
 * Identifiers can be either the Object's [name], or one or more [Identifier] key-value pairs.
 * In order for an 'Identifier' to be used for identification, it must have
 * [isPartOfUniqueness][Identifier.isPartOfUniqueness] set to true (this is the default).
 *
 * Two Objects with the same Key are not permitted in a [CollectResult].
 *
 * Objects must be created with the full key. Keys cannot change after the Object has been created.
 *
 * All Objects with the same Adapter Type and Object Type must have the same set of Identifiers.
 *
 * @property adapterType The Adapter Type this Object is associated with.
 * @property objectType The Object Type (e.g., class) of this Object.
 * @property name A human-readable name for this Object. Should be unique if possible.
 * @property identifiers A list of [Identifiers][Identifier] that uniquely identify the Object. If none are present than
 * the name must be unique and is used for identification. All Objects with the same adapter type and Object
 * type must have the same set of identifiers.
 */
@Serializable
class Key @OptIn(ExperimentalSerializationApi::class)
@JvmOverloads constructor(
    @SerialName("adapter_kind") val adapterType: String,
    @SerialName("object_kind") val objectType: String,
    val name: String,
    @EncodeDefault(EncodeDefault.Mode.ALWAYS) val identifiers: List<Identifier> = emptyList(),
) {
    @Transient private val identifierMap = identifiers.associateBy(Identifier::key)

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
                identifiers.filter { identifier -> identifier.isPartOfUniqueness }
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
    override fun equals(other: Any?) = other is Key && internalKey == other.internalKey

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
        val value = identifierMap[key]?.value
        return if (value?.isBlank() != false) {
            defaultValue ?: value
        } else {
            value
        }
    }
}
