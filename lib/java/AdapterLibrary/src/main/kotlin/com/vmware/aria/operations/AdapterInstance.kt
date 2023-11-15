/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.decodeFromJsonElement
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

@Serializable
data class CredentialField(
    val key: String,
    val value: String,
    @SerialName("is_password") val isPassword: Boolean,
)

@Serializable
class Credential(
    /**
     * Get the type (key) of credential. This is useful if an adapter supports multiple
     * types of credentials.
     *
     * @return The type of the credential used by this adapter instance, or null if the
     * adapter instance does not have a credential.
     */
    @SerialName("credential_key") val type: String?,
    @SerialName("credential_fields") private val fields: List<CredentialField>,
) : Map<String, String> by fields.associate({ field -> Pair(field.key, field.value) })

/**
 * Class that represents a list of validated SSL certificates that have been verified
 * automatically by a CA or manually by the user.
 */
@Serializable
class Certificates(private val certificates: List<String>) :
    List<String> by certificates

/**
 * Class that describes a time window. In some cases, it is useful to have a start and end time
 * for collection. The CollectionWindow's [startTime] and [endTime] will be modified each collection
 * such that each collection's [endTime] will be the next collection's [startTime]. Thus, the window
 * can be treated as either the interval `(startTime, endTime]` or `[startTime, endTime)`, so long
 * as each collection uses the same convention, there will be no overlaps or missing times. (Note
 * that restarting the adapter instance will reset the time window. In general, this will cause
 * overlap and/or missing times when restarts occur for any reason)
 */
@Serializable
data class CollectionWindow(
    /**
     * The start of the window. On the first collection, this will be set to `0`.
     */
    @SerialName("start_time") val startTime: Double,
    /**
     * The end of the window
     */
    @SerialName("end_time") val endTime: Double,
)

class AdapterInstance(json: JsonObject) : Object(getKey(json)) {
    /**
     * Gets information about the credential (if it exists) for this Adapter Instance
     */
    val credential: Credential

    /**
     * Gets an authenticated [Suite API Client][SuiteApiClient].
     */
    val suiteApiClient: SuiteApiClient

    /**
     * Gets the list of SSL Certificates that have been verified automatically by a CA
     * or manually by the user.
     */
    val certificates: Certificates

    /**
     * Gets the current collection number, starting from 0.
     */
    val collectionNumber: Int

    /**
     * Gets the current collection window.
     */
    val collectionWindow: CollectionWindow

    init {
        credential = json["credential_config"]?.let {
            Json.decodeFromJsonElement(it)
        } ?: Credential(null, emptyList())

        suiteApiClient = SuiteApiClient(
            when (val suiteApiConnectionInfo = json["cluster_connection_info"]) {
                is JsonNull, null -> SuiteApiConnectionInfo("", "", "")
                else -> Json.decodeFromJsonElement<SuiteApiConnectionInfo>(
                    suiteApiConnectionInfo
                )
            }
        )

        certificates = json["certificate_config"]?.let {
            Json.decodeFromJsonElement(it)
        } ?: Certificates(emptyList())

        collectionNumber = json["collection_number"]?.jsonPrimitive?.intOrNull ?: 0
        collectionWindow = json["collection_window"]?.let {
            Json.decodeFromJsonElement(it)
        } ?: CollectionWindow(0.0, System.currentTimeMillis().toDouble())
    }

    /**
     * @return The type (key) of the credential, or `null` if this Adapter Instance does
     * not have a credential.
     */
    fun getCredentialType(): String? = credential.type

    /**
     * Retrieve the value of a given credential
     * @param key Key of the credential field
     * @return value associated with the credential field, or null if a credential field
     * with the given key does not exist.
     */
    fun getCredentialValue(key: String): String? = credential[key]

    companion object {
        /**
         * Create an [AdapterInstance] from the input pipe.
         */
        @JvmStatic
        @JvmOverloads
        fun fromInput(inputFile: String = Pipes.input): AdapterInstance {
            val json = readFromPipe(inputFile)
                ?: throw IllegalArgumentException("Cannot read Adapter Instance from input")
            return AdapterInstance(json.jsonObject)
        }


        private fun getKey(json: JsonObject): Key {
            return json["adapter_key"]?.jsonObject?.let { adapterKey ->
                Key(
                    adapterType = adapterKey["adapter_kind"]?.jsonPrimitive?.content
                        ?: "",
                    objectType = adapterKey["object_kind"]?.jsonPrimitive?.content
                        ?: "",
                    name = adapterKey["name"]?.jsonPrimitive?.content ?: "",
                    identifiers = adapterKey["identifiers"]?.jsonArray?.map { identifier ->
                        Identifier(
                            identifier.jsonObject["key"]?.jsonPrimitive?.content ?: "",
                            identifier.jsonObject["value"]?.jsonPrimitive?.content
                                ?: "",
                            identifier.jsonObject["is_part_of_uniqueness"]?.jsonPrimitive?.boolean
                                ?: true
                        )
                    } ?: listOf()
                )
            }
                ?: throw IllegalArgumentException("Cannot read Adapter Instance Key from input")
        }
    }
}
