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
import java.util.function.Consumer

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
        val field = CredentialStringParameter(key, label, required, credentialParameters.size)
        addParameter(field)
        return field
    }

    /**
     * Create a new string parameter and add it to the credential definition. The user will be asked to provide a value for
     * this parameter each time a new credential is created.
     * @param key Used to identify the credential parameter
     * @param block Anonymous function taking a CredentialStringParameterBuilder as a parameter that can be used to override
     * default values. This is particularly useful in Java.
     */
    @Throws(DuplicateKeyException::class)
    fun defineStringParameter(key: String, block: Consumer<CredentialStringParameterBuilder>): CredentialStringParameter {
        val parameterBuilder = CredentialStringParameterBuilder(key)
        block.accept(parameterBuilder)
        val parameter = parameterBuilder.build(credentialParameters.size)
        addParameter(parameter)
        return parameter
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
        val field = CredentialIntParameter(key, label, required, credentialParameters.size)
        addParameter(field)
        return field
    }

    /**
     * Create a new integer parameter and add it to the credential definition. The user will be asked to provide a value for
     * this parameter each time a new credential is created.
     * @param key Used to identify the credential parameter
     * @param block Anonymous function taking a CredentialIntegerParameterBuilder as a parameter that can be used to override
     * default values. This is particularly useful in Java.
     */
    @Throws(DuplicateKeyException::class)
    fun defineIntParameter(key: String, block: Consumer<CredentialIntParameterBuilder>): CredentialIntParameter {
        val parameterBuilder = CredentialIntParameterBuilder(key)
        block.accept(parameterBuilder)
        val parameter = parameterBuilder.build(credentialParameters.size)
        addParameter(parameter)
        return parameter
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
        val field = CredentialPasswordParameter(key, label, required, credentialParameters.size)
        addParameter(field)
        return field
    }

    /**
     * Create a new password parameter and add it to the credential definition. The user will be asked to provide a value for
     * this parameter each time a new credential is created.
     * @param key Used to identify the credential parameter
     * @param block Anonymous function taking a CredentialPasswordParameterBuilder as a parameter that can be used to override
     * default values. This is particularly useful in Java.
     */
    @Throws(DuplicateKeyException::class)
    fun definePasswordParameter(key: String, block: Consumer<CredentialPasswordParameterBuilder>): CredentialPasswordParameter {
        val parameterBuilder = CredentialPasswordParameterBuilder(key)
        block.accept(parameterBuilder)
        val parameter = parameterBuilder.build(credentialParameters.size)
        addParameter(parameter)
        return parameter
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
        val field = CredentialEnumParameter(key, values, label, default, required, credentialParameters.size)
        addParameter(field)
        return field
    }

    /**
     * Create a new enum parameter and add it to the credential definition. The user will be asked to provide a value for
     * this parameter each time a new credential is created.
     * @param key Used to identify the credential parameter
     * @param block Anonymous function taking a CredentialEnumParameterBuilder as a parameter that can be used to override
     * default values. This is particularly useful in Java.
     */
    @Throws(DuplicateKeyException::class)
    fun defineEnumParameter(key: String, block: Consumer<CredentialEnumParameterBuilder>): CredentialEnumParameter {
        val parameterBuilder = CredentialEnumParameterBuilder(key)
        block.accept(parameterBuilder)
        val parameter = parameterBuilder.build(credentialParameters.size)
        addParameter(parameter)
        return parameter
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
    open val displayOrder: Int = 0

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

/**
 * @param key Used to identify the parameter.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param required True if user is required to provide this parameter. Defaults to True.
 */
class CredentialIntParameter @JvmOverloads constructor(override val key: String, override val label: String = key, override val required: Boolean = true, override val displayOrder: Int = 0):
    CredentialParameter() {
    override val type = "integer"
}

/**
 * @property key Used to identify the parameter.
 * @property label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @property required True if user is required to provide this parameter. Defaults to True.
 */
class CredentialIntParameterBuilder(val key: String) {
    var label: String = key
    var required: Boolean = true
    fun build(displayOrder: Int) = CredentialIntParameter(key, label, required, displayOrder)
}

/**
 * @param key Used to identify the parameter.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param required True if user is required to provide this parameter. Defaults to True.
 */
class CredentialStringParameter @JvmOverloads constructor(override val key: String, override val label: String = key, override val required: Boolean = true, override val displayOrder: Int = 0):
    CredentialParameter() {
    override val type = "string"
}

/**
 * @property key Used to identify the parameter.
 * @property label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @property required True if user is required to provide this parameter. Defaults to True.
 */
class CredentialStringParameterBuilder(val key: String) {
    var label: String = key
    var required: Boolean = true
    fun build(displayOrder: Int) = CredentialStringParameter(key, label, required, displayOrder)
}

/**
 * @param key Used to identify the parameter.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param required True if user is required to provide this parameter. Defaults to True.
 */
class CredentialPasswordParameter @JvmOverloads constructor(override val key: String, override val label: String = key, override val required: Boolean = true, override val displayOrder: Int = 0):
    CredentialParameter() {
    override val type = "string"
    override val password = true
}

/**
 * @property key Used to identify the parameter.
 * @property label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @property required True if user is required to provide this parameter. Defaults to True.
 */
class CredentialPasswordParameterBuilder(val key: String) {
    var label: String = key
    var required: Boolean = true
    fun build(displayOrder: Int) = CredentialPasswordParameter(key, label, required, displayOrder)
}

/**
 * @param key Used to identify the parameter.
 * @param values An array containing all enum values. If [default] is specified and not part of the array,
 * it will be added as an additional enum value.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param required True if user is required to provide this parameter. Defaults to True.
 * @param displayOrder
 */
class CredentialEnumParameter @JvmOverloads constructor(override val key: String, val values: List<EnumParameter.EnumValue>, override val label: String = key, val default: String? = null, override val required: Boolean = true, override val displayOrder: Int = 0): CredentialParameter() {
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

/**
 * @property key Used to identify the parameter.
 * @property label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 */
class CredentialEnumParameterBuilder(val key: String) {
    var label: String = key
    private val values: MutableList<EnumParameter.EnumValue> = mutableListOf()
    private var default: String? = null

    /**
     * Adds an option to the Enum Parameter
     * @param key The key of the Enum
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     */
    @JvmOverloads
    fun withOption(key: String, label: String = key) {
        values.add(EnumParameter.EnumValue(key, label))
    }

    /**
     * Adds an option to the Enum Parameter, and sets it as the default option. This should
     * only be called once per parameter. If it is called multiple times, the default will be
     * set to the value of the last call.
     *
     * @param key The key of the Enum
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     */
    @JvmOverloads
    fun withDefaultOption(key: String, label: String = key) {
        values.add(EnumParameter.EnumValue(key, label))
        default = key
    }
    var required: Boolean = true
    fun build(displayOrder: Int) = CredentialEnumParameter(key, values, label, default, required, displayOrder)
}
