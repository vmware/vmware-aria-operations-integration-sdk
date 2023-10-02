/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations.definition
import com.vmware.aria.operations.DuplicateKeyException
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.addJsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray

class CredentialType @JvmOverloads constructor(
    val key: String,
    val label: String = key
) {
    private val credentialParameters = mutableMapOf<String, CredentialParameter>()

    /**
    * Create a new string credential parameter and apply it to this credential definition.
    *
    * @param key Used to identify the parameter.
    * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
    * @param required True if user is required to provide this parameter. Defaults to True.

    * @return The created string parameter definition.
    */
    @Throws(DuplicateKeyException::class)
    @JvmOverloads
    fun defineStringParameter(
        key: String,
        label: String = key,
        required: Boolean = true
    ): CredentialStringParameter {
        val field = CredentialStringParameter(key, label, required)
        addParameter(field)
        return field
    }

    /**
     * Create a new integer credential parameter and apply it to this credential definition.
     *
     * @param key Used to identify the parameter.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param required True if user is required to provide this parameter. Defaults to True.

     * @return The created integer parameter definition.
     */
    @Throws(DuplicateKeyException::class)
    @JvmOverloads
    fun defineIntParameter(
        key: String,
        label: String = key,
        required: Boolean = true
    ): CredentialIntParameter {
        val field = CredentialIntParameter(key, label, required)
        addParameter(field)
        return field
    }

    /**
     * Create a new password credential parameter and apply it to this credential definition.
     *
     * @param key Used to identify the parameter.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param required True if user is required to provide this parameter. Defaults to True.

     * @return The created password parameter definition.
     */
    @Throws(DuplicateKeyException::class)
    @JvmOverloads
    fun definePasswordParameter(
        key: String,
        label: String = key,
        required: Boolean = true
    ): CredentialPasswordParameter {
        val field = CredentialPasswordParameter(key, label, required)
        addParameter(field)
        return field
    }

    /**
     * Create a new enum credential parameter and apply it to this credential definition.
     *
     * @param key Used to identify the parameter.
     * @param values A [List] containing all enum values. If [default] is specified
     * and not part of this list, it will be added as an additional enum value.
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param required True if user is required to provide this parameter. Defaults to True.

     * @return The created enum parameter definition.
     */
    @Throws(DuplicateKeyException::class)
    @JvmOverloads
    fun defineEnumParameter(
        key: String,
        values: List<EnumParameter.EnumValue>,
        label: String = key,
        default: String? = null,
        required: Boolean = true
    ): CredentialEnumParameter {
        val field = CredentialEnumParameter(key, values, label, default, required)
        addParameter(field)
        return field
    }

    /**
     * @param parameters A list of parameters to add to the credential
    */
    @Throws(DuplicateKeyException::class)
    fun addParameters(parameters: Collection<CredentialParameter>) {
        parameters.forEach { parameter ->
            addParameter(parameter)
        }
    }

    /**
     * @param parameter A parameter to add to the credential
     */
    @Throws(DuplicateKeyException::class)
    fun addParameter(parameter: CredentialParameter) {
        val key = parameter.key
        if (credentialParameters.containsKey(key)) {
            throw DuplicateKeyException("Credential field with key $key already exists in Adapter Definition.")
        }
        parameter.displayOrder = credentialParameters.size
        credentialParameters[key] = parameter
    }

    val json: JsonObject
        get() = buildJsonObject {
            put("key", key)
            put("label", label)
            putJsonArray("fields") {
                credentialParameters.values.forEach { field ->
                    add(field.json)
                }
            }
        }
}

sealed class CredentialParameter {
    abstract val key: String
    abstract val label: String
    abstract val type: String
    abstract val required: Boolean
    open val password = false
    open val enum = false
    var displayOrder: Int = 0
        internal set

    open val json: JsonObject
        get() = buildJsonObject {
            put("key", key)
            put("label", label)
            put("type", type)
            put("enum", enum)
            put("password", password)
            put("required", required)
            put("display_order", displayOrder)
        }
}

class CredentialIntParameter @JvmOverloads constructor(override val key: String, override val label: String = key, override val required: Boolean = true):
    CredentialParameter() {
    override val type = "integer"
}

class CredentialStringParameter @JvmOverloads constructor(override val key: String, override val label: String = key, override val required: Boolean = true):
    CredentialParameter() {
    override val type = "string"
}

class CredentialPasswordParameter @JvmOverloads constructor(override val key: String, override val label: String = key, override val required: Boolean = true):
    CredentialParameter() {
    override val type = "string"
    override val password = true
}

class CredentialEnumParameter @JvmOverloads constructor(override val key: String, val values: List<EnumParameter.EnumValue>, override val label: String = key, val default: String? = null, override val required: Boolean = true): CredentialParameter() {
    override val type = "string"
    override val enum = true

    override val json: JsonObject
        get() = extendJsonObject(super.json) {
            putJsonArray("enum_values") {
                val allValues = values.toMutableList()
                default?.let { default ->
                    if (allValues.firstOrNull { it.key == default } == null) {
                        allValues.add(0, EnumParameter.EnumValue(default, default))
                    }
                }
                allValues.forEachIndexed { index, enum ->
                    addJsonObject {
                        put("key", enum.key)
                        put("label", enum.label)
                        put("display_order", index)
                    }
                }
            }
        }
}
