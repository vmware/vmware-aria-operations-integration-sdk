/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations.definition

import com.vmware.aria.operations.DuplicateKeyException
import com.vmware.aria.operations.KeyException
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray

/**
 * Create a new object type definition
 *
 * @property key A key used to identify the object type
 * @property label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 */
class ObjectType @JvmOverloads @Throws(KeyException::class) constructor(
    override val key: String,
    val label: String = key,
) : GroupType() {
    init {
        if (key.isBlank()) {
            throw KeyException("Object type key cannot be empty.")
        }
    }
    private val identifierMap = LinkedHashMap<String, Parameter>()

    /**
     * Create a new string identifier and apply it to this object type definition.
     * All identifiers marked as 'part of uniqueness' are used to determine object identification. If none exist, the
     * object name will be used for identification.
     *
     * @param key Used to identify the parameter.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param required True if this parameter is required. Defaults to True.
     * @param isPartOfUniqueness True if the parameter should be used for object identification. Defaults to True.
     * @param default The default value of the parameter.
     *
     * @return The created String Identifier.
     */
    fun defineStringIdentifier(
        key: String,
        label: String = key,
        required: Boolean = true,
        isPartOfUniqueness: Boolean = true,
        default: String? = null,
    ): ObjectType = this.apply {
        val parameter = StringParameter(
            key,
            label,
            required = required,
            advanced = !isPartOfUniqueness,
            default = default,
            displayOrder = identifierMap.size,
        )
        addIdentifier(parameter)
    }

    /**
     * Create a new integer identifier and apply it to this object type definition.
     * All identifiers marked as 'part of uniqueness' are used to determine object identification. If none exist, the
     * object name will be used for identification.
     *
     * @param key Used to identify the parameter.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param required True if this parameter is required. Defaults to True.
     * @param isPartOfUniqueness True if the parameter should be used for object identification. Defaults to True.
     * @param default The default value of the parameter.
     *
     * @return The created Integer Identifier.
     */
    fun defineIntIdentifier(
        key: String,
        label: String = key,
        required: Boolean = true,
        isPartOfUniqueness: Boolean = true,
        default: Int? = null,
    ): ObjectType = this.apply {
        val parameter = IntParameter(
            key,
            label,
            required = required,
            advanced = !isPartOfUniqueness,
            default = default,
            displayOrder = identifierMap.size,
        )
        addIdentifier(parameter)
    }

    /**
     * Create a new enum identifier and apply it to this object type definition.
     * All identifiers marked as 'part of uniqueness' are used to determine object identification. If none exist, the
     * object name will be used for identification.
     *
     * @param key Used to identify the parameter.
     * @param values A List containing all enum values. If [default] is specified and not part of this list, it
     * will be added as an additional enum value. Values are case-sensitive. Enum values are not localizable.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param required True if this parameter is required. Defaults to True.
     * @param isPartOfUniqueness True if the parameter should be used for object identification. Defaults to True.
     * @param default The default value of the parameter.
     *
     * @return The created Integer Identifier.
     */
    fun defineEnumIdentifier(
        key: String,
        values: List<EnumParameter.EnumValue>,
        label: String = key,
        required: Boolean = true,
        isPartOfUniqueness: Boolean = true,
        default: String? = null,
    ): ObjectType = this.apply {
        val parameter = EnumParameter(
            key,
            values,
            label,
            required = required,
            advanced = !isPartOfUniqueness,
            default = default,
            displayOrder = identifierMap.size,
        )
        addIdentifier(parameter)
    }

    /**
     * @param identifiers A collection of identifiers to add to this [ObjectType].
     */
    fun addIdentifiers(identifiers: Iterable<Parameter>) {
        identifiers.forEach { identifier ->
            addIdentifier(identifier)
        }
    }

    /**
     * Add an identifier to this object type. All 'identifying' identifiers are used to determine object uniqueness.
     * If no 'identifying' identifiers exist, they object name will be used for uniqueness.
     *
     * @param identifier The identifier to add to the object type definition.
     */
    fun addIdentifier(identifier: Parameter) {
        val key = identifier.key
        if (identifierMap.containsKey(key)) {
            throw DuplicateKeyException("Identifier with key $key already exists in object type ${this.key}.")
        }
        identifierMap[key] = identifier
    }

    override val json: JsonObject
        get() = extendJsonObject(super.json) {
            put("key", key)
            put("label", label)
            putJsonArray("identifiers") {
                identifierMap.values.forEach { identifier ->
                    add(identifier.json)
                }
            }
        }
}