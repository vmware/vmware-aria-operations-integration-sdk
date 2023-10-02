/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations.definition

import com.vmware.aria.operations.DuplicateKeyException
import com.vmware.aria.operations.KeyException
import com.vmware.aria.operations.Pipes
import com.vmware.aria.operations.writeToPipe
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray


class AdapterDefinition
@Throws(KeyException::class)
@JvmOverloads constructor(
    val adapterType: String,
    val adapterLabel: String = adapterType,
    val adapterInstanceType: String = "${adapterType}_adapter_instance",
    val adapterInstanceLabel: String = "$adapterLabel Adapter Instance",
    val version: Int = 1,
) : GroupType() {
    override val key: String
        get() = adapterInstanceType
    private val parameters: MutableMap<String, Parameter> = LinkedHashMap()
    private val credentials = mutableMapOf<String, CredentialType>()
    private val objectTypes = mutableMapOf<String, ObjectType>()

    init {
        if (adapterType.isBlank()) {
            throw KeyException("Adapter type cannot be blank.")
        }
        if (!adapterType[0].isLetter()) {
            throw KeyException("Adapter type must start with a letter.")
        }
        if (!adapterType.matches("""^[a-zA-Z0-9_]*$""".toRegex())) {
            throw KeyException("Adapter type cannot contain whitespace or special characters besides '_'.")
        }
        if (adapterInstanceType.isBlank()) {
            throw KeyException("Adapter Instance Type cannot be blank.")
        }
    }

    /**
    * Create a new string parameter and add it to the adapter instance. The user will be asked to provide a value for
    * this parameter each time a new account/adapter instance is created.
    *
    * @param key Used to identify the parameter
    * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
    * @param description More in-depth explanation of the parameter. Displayed as a tooltip in the
    * VMware Aria Operations UI.
    * @param default The default value of the parameter. Defaults to None
    * @param maxLength The max length of the parameter value. Defaults to 512.
    * @param required True if user is required to provide this parameter. Defaults to True.
    * @param advanced True if the parameter should be collapsed by default. Defaults to False.
    *
    * @return The created string parameter definition.
    */
    @JvmOverloads
    @Throws(DuplicateKeyException::class)
    fun defineStringParameter(
        key: String,
        label: String = key,
        description: String? = null,
        default: String? = null,
        maxLength: Int = 512,
        required: Boolean = true,
        advanced: Boolean = false
    ): StringParameter {
        val parameter = StringParameter(key, label, description, default, maxLength, required, advanced)
        addParameter(parameter)
        return parameter
    }

    /**
    * Create a new integer parameter and add it to the adapter instance. The user will be asked to provide a value for
    * this parameter each time a new account/adapter instance is created.
    *
    * @param key Used to identify the parameter
    * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
    * @param description More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
    * @param default The default value of the parameter.
    * @param required True if user is required to provide this parameter. Defaults to True.
    * @param advanced True if the parameter should be collapsed by default. Defaults to False.
    *
    * @return The created int parameter definition.
    */
    @JvmOverloads
    @Throws(DuplicateKeyException::class)
    fun defineIntegerParameter(
        key: String,
        label: String = key,
        description: String? = null,
        default: Int? = null,
        required: Boolean = true,
        advanced: Boolean = false
    ): IntParameter {
        val parameter = IntParameter(key, label, description, default, required, advanced)
        addParameter(parameter)
        return parameter
    }

    /**
     * Create a new enum parameter and add it to the adapter instance. The user will be asked to provide a value for
     * this parameter each time a new account/adapter instance is created.
     *
     * @param key Used to identify the parameter
     * @param values A [List] containing all enum values. If [default] is specified and not part of this list, it
     * will be added as an additional enum value (values are case-sensitive).
     * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
     * @param description More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
     * @param default The default value of the parameter.
     * @param required True if user is required to provide this parameter. Defaults to True.
     * @param advanced True if the parameter should be collapsed by default. Defaults to False.
     *
     * @return The created int parameter definition.
     */
    @JvmOverloads
    @Throws(DuplicateKeyException::class)
    fun defineEnumParameter(
        key: String,
        values: List<EnumParameter.EnumValue>,
        label: String = key,
        description: String? = null,
        default: String? = null,
        required: Boolean = true,
        advanced: Boolean = false
    ): EnumParameter {
        val parameter = EnumParameter(key, values, label, description, default, required, advanced)
        addParameter(parameter)
        return parameter
    }

    /**
    * Add a parameter to the adapter instance. The user will be asked to provide a value for
    * this parameter each time a new account/adapter instance is created.
    *
    * @param parameter The parameter to add to the adapter instance.
    */
    @Throws(DuplicateKeyException::class)
    fun addParameter(parameter: Parameter) {
        val key = parameter.key
        if (parameters.containsKey(key)) {
            throw DuplicateKeyException("Parameter with Key $key already exists in Adapter Definition.")
        }
        parameters[key] = parameter
    }

    /**
    * Create a new credential type and add it to this adapter instance. When more than one credential types are
    * present, The user will be required to select the type and then fill in the parameters for that type, as only
    * one credential type can be used for any given adapter instance.
    *
    * @param key Used to identify the credential type
    * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
    *
    * @return The created credential type.
    */
    @JvmOverloads
    @Throws(DuplicateKeyException::class)
    fun defineCredentialType(key: String = "default_credential", label: String = key): CredentialType {
        val credential = CredentialType(key, label)
        addCredentialType(credential)
        return credential
    }

    /**
    * Add a list of credential types to the adapter instance.
    *
    * @param credentialTypes A list of credential types to add.
    */
    @Throws(DuplicateKeyException::class)
    fun addCredentialTypes(credentialTypes: List<CredentialType>) {
        credentialTypes.forEach { credentialType ->
            addCredentialType(credentialType)
        }
    }

    /**
    * Add a credential type to the adapter instance. When more than one credential types are present, The user will
    * be required to select the type and then fill in the parameters for that type, as only one credential type can be
    * used for any given adapter instance.
    *
    * @param credentialType The credential type to add.
    */
    @Throws(DuplicateKeyException::class)
    fun addCredentialType(credentialType: CredentialType) {
        val key = credentialType.key
        if(credentials.containsKey(key)) {
            throw DuplicateKeyException (
                    "Credential type with key $key already exists in Adapter Definition."
            )
        }
        credentials[key] = credentialType
    }

    /**
    * Create a new object type definition and add it to this adapter definition.
    *
    * @param key The object type
    * @param label Label that is displayed in the VMware Aria Operations UI for this object type. Defaults to the key.
    *
    * @return The created object type definition
    */
    @Throws(DuplicateKeyException::class)
    fun defineObjectType(key: String, label: String = key): ObjectType
    {
        val objectType = ObjectType(key, label)
        addObjectType(objectType)
        return objectType
    }

    /**
    * Adds a list of object types to this adapter definition
     *
    * @param objectTypes A list of object type definitions.
    */
    @Throws(DuplicateKeyException::class)
    fun addObjectTypes(objectTypes: List<ObjectType>) {
        objectTypes.forEach { objectType ->
            addObjectType(objectType)
        }
    }

    /**
    * Adds an object type to this adapter definition
     *
    * @param objectType An object type definition.
    */
    @Throws(DuplicateKeyException::class)
    fun addObjectType(objectType: ObjectType) {
        val key = objectType.key
        if (objectTypes.containsKey(key)) {
            throw DuplicateKeyException (
                    "Object type with key $key already exists in Adapter Definition."
            )
        }
        objectTypes[key] = objectType
    }

    override val json: JsonObject
        get() = buildJsonObject {
            put("adapter_key", adapterType)
            put("adapter_label", adapterLabel)
            put("describe_version", version)
            put("schema_version", 1)
            put("adapter_instance", extendJsonObject(super.json) {
                put("key", adapterInstanceType)
                put("label", adapterInstanceLabel)
                putJsonArray("identifiers") {
                    parameters.values.forEach { parameter ->
                        add(parameter.json)
                    }
                }
            })
            putJsonArray("credential_types") {
                credentials.values.forEach {credential ->
                    add(credential.json)
                }
            }
            putJsonArray("object_types") {
                objectTypes.values.forEach {objectType ->
                    add(objectType.json)
                }
            }
        }

    /**
     * Opens the output pipe and sends the definition directly back to the server
     * This method can only be called once per collection.
     * @param outputPipe The path to the output pipe.
     */
    @JvmOverloads
    fun sendResults(outputPipe: String = Pipes.output) {
        writeToPipe(json, outputPipe)
    }
}