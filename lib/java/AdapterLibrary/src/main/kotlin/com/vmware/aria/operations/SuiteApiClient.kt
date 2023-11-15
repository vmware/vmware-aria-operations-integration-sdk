/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.cio.CIO
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.accept
import io.ktor.client.request.delete
import io.ktor.client.request.get
import io.ktor.client.request.header
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.HttpResponse
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.Transient
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.encodeToJsonElement
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.apache.logging.log4j.Logger
import java.security.cert.X509Certificate
import javax.net.ssl.X509TrustManager
import kotlin.math.ceil
import kotlin.math.roundToInt
import kotlin.reflect.KProperty

/**
 * Class to hold Suite API connection information
 * @property hostname The hostname or IP address of the SuiteAPI
 * @property username The username to connect with
 * @property password The username's password
 * @property port Determines the port to connect to the server with. Used for testing.
 * @property verify Determines if the SSL Certificate from the server should be verified. Used for testing.
 */
@Serializable
data class SuiteApiConnectionInfo @JvmOverloads constructor(
    @SerialName("host_name") val hostname: String,
    @SerialName("user_name") val username: String,
    val password: String,
    val port: Int = 443,
    val verify: Boolean = false,
) {
    @Transient
    private val baseUrl: String = getBaseUrl()

    @Transient
    internal val authenticationSource = "LOCAL"

    private fun getBaseUrl(): String {
        var url = hostname
        if (!url.startsWith("https://")) {
            url = "https://$url"
        }
        if (url.endsWith(URL_PATH_SEPARATOR)) {
            url = url.substringBefore(URL_PATH_SEPARATOR)
        }
        url = "$url:$port$URL_PATH_SEPARATOR"
        return url
    }

    /**
     * Given an API endpoint, prepend the protocol and hostname. If the endpoint does not
     * include 'suite-api/', that is added between the hostname and endpoint (unless the
     * endpoint is an internal API).
     * @param endpoint Endpoint to turn into a full URL
     * @return Full URL of the given endpoint
     */
    fun getUrl(endpoint: String): String {
        if (!endpoint.contains("suite-api") && !endpoint.contains("internal")) {
            "${baseUrl}suite-api$URL_PATH_SEPARATOR"
        } else {
            baseUrl
        }.let { baseUrl ->
            return if (baseUrl.endsWith(URL_PATH_SEPARATOR) &&
                endpoint.startsWith(URL_PATH_SEPARATOR)
            ) {
                "${baseUrl.dropLast(1)}$endpoint"
            } else if (baseUrl.endsWith(URL_PATH_SEPARATOR) ||
                endpoint.startsWith(URL_PATH_SEPARATOR)
            ) {
                "$baseUrl$endpoint"
            } else {
                "$baseUrl${URL_PATH_SEPARATOR}$endpoint"
            }
        }
    }

    companion object {
        private const val URL_PATH_SEPARATOR = "/"
    }
}

/**
 * Gets a new SuiteAPI Authentication token if one does not exist, or if the current
 * token will expire within 10 seconds
 * @property logger A logger
 * @property client An HTTP Client used for requesting and deleting tokens
 * @property connectionInfo A [SuiteApiConnectionInfo] class containing the Suite API host and credentials
 */
private class TokenDelegate(
    private val logger: Logger,
    private val client: HttpClient,
    private val connectionInfo: SuiteApiConnectionInfo,
) {
    /**
     * Class representing the Json body of the post request for acquiring a token
     */
    @Serializable
    private data class RequestBody(
        val username: String,
        val password: String,
        val authSource: String,
    )

    /**
     * Class representing the Json response of the post request for acquiring a token
     */
    @Serializable
    private data class TokenInfo(
        val validity: Long,
        val token: String,
        val expiresAt: String,
        val roles: List<String>,
    )

    private var tokenInfo: TokenInfo? = null
    private val requestBody = RequestBody(
        connectionInfo.username,
        connectionInfo.password,
        connectionInfo.authenticationSource
    )
    private val mutex = Mutex()

    /**
     * Returns true if a token exists and will not expire within the next 10 seconds
     */
    private fun isValid(): Boolean = tokenInfo?.let { token ->
        // Add 10 seconds so that the token won't expire between retrieval and use
        token.validity > System.currentTimeMillis() + 10_000L
    } ?: false

    /**
     * Returns the token if it exists, or requests one if it does not exist. If multiple
     * requests for the token are made concurrently, only the first will request a token,
     * and the other requests will wait until that request has completed.
     */
    operator fun getValue(thisRef: Any?, property: KProperty<*>): String =
        runBlocking {
            mutex.withLock {
                if (!isValid()) {
                    logger.debug("Requesting New Token")
                    tokenInfo =
                        client.post(connectionInfo.getUrl("api/auth/token/acquire")) {
                            accept(ContentType.Application.Json)
                            contentType(ContentType.Application.Json)
                            setBody(requestBody)
                        }.throwOnErrorStatus().body()
                }
                return@runBlocking tokenInfo?.token ?: ""
            }
        }

    /**
     * Releases a token, so that it is no longer valid.
     */
    fun releaseToken(): Unit = runBlocking {
        logger.debug("Releasing Token")
        if (isValid()) {
            client.post(connectionInfo.getUrl("/api/auth/token/release")) {
                contentType(ContentType.Application.Json)
                accept(ContentType.Application.Json)
                header(
                    "Authorization",
                    "vRealizeOpsToken ${tokenInfo?.token}"
                )
            }
        }
        tokenInfo = null
    }
}

/**
 * Class that simplifies making calls to VMware Aria Operations' Suite API
 * @property connectionInfo Connection and credential information for connecting to the SuiteAPI
 * @property maxConnections The maximum number of concurrent connections allowed. Defaults to 10
 */
class SuiteApiClient @JvmOverloads constructor(
    val connectionInfo: SuiteApiConnectionInfo,
    maxConnections: Int = 10,
) : AutoCloseable {
    private val client = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                prettyPrint = true
                isLenient = true
            })
        }
        if (!connectionInfo.verify) {
            engine {
                https {
                    trustManager = object : X509TrustManager {
                        override fun checkClientTrusted(
                            chain: Array<out X509Certificate>?,
                            authType: String?,
                        ) = Unit

                        override fun checkServerTrusted(
                            chain: Array<out X509Certificate>?,
                            authType: String?,
                        ) = Unit

                        override fun getAcceptedIssuers(): Array<X509Certificate> =
                            emptyArray()

                    }
                }
            }
        }
    }
    private val tokenDelegate = TokenDelegate(getLogger(), client, connectionInfo)
    private val token by tokenDelegate
    private val logger = getLogger()
    private var throttler = Semaphore(maxConnections)

    /**
     * Sets the maximum number of concurrent connections allowed. The default value is 10.
     * Note: Any existing connections when this method is called will not be bound
     * by the new limit.
     * @param maxConnections The maximum number of concurrent connections allowed.
     */
    var maxConnections: Int = maxConnections
        set(maxConnections: Int) {
            if (field != maxConnections) {
                field = maxConnections
                this.throttler = Semaphore(field)
            }
        }

    /**
     * Performs a GET operation on the given endpoint.
     * @param endpoint The API endpoint to call
     * @return A [JsonObject] containing the content as a json object. Throws if the
     * response code is not 2xx.
     */
    @Throws(SuiteApiClientException::class)
    fun get(endpoint: String): JsonObject =
        runBlocking {
            getAsync(endpoint)
        }

    /**
     * A Kotlin [suspend] method that performs a GET operation on the given endpoint.
     * @param endpoint The API endpoint to call
     * @return A [JsonObject] containing the content as a json object. Throws if the
     * response code is not 2xx.
     */
    @Throws(SuiteApiClientException::class)
    suspend fun getAsync(endpoint: String): JsonObject {
        return getRawResponseAsync(endpoint).throwOnErrorStatus().toJson()
    }

    /**
     * Performs a GET operation on the given endpoint.
     * @param endpoint The API endpoint to perform a get request on
     */
    fun getRawResponse(endpoint: String): HttpResponse =
        runBlocking {
            getRawResponseAsync(endpoint)
        }

    /**
     * A Kotlin [suspend] method that performs a GET operation on the given endpoint.
     * @param endpoint The API endpoint to call
     * @return An [HttpResponse] containing the return code and content
     */
    suspend fun getRawResponseAsync(endpoint: String): HttpResponse {
        return throttler.throttleCall {
            client.get(connectionInfo.getUrl(endpoint)) {
                accept(ContentType.Application.Json)
                header("Authorization", "vRealizeOpsToken $token")
                if (endpoint.contains("internal")) {
                    logger.debug("Using unsupported API: $endpoint")
                    header("X-vRealizeOps-API-use-unsupported", true)
                }
            }
        }
    }

    /**
     * A method that performs a paged GET operation on the given endpoint.
     * After the first GET operation succeeds, subsequent GET requests will be done
     * concurrently (with a max of [maxConnections] concurrent requests) until all of
     * paged data has been retrieved.
     * @param endpoint The API endpoint to call
     * @param pagedArrayKey The key on each returned json object to combine. This key should
     * contain a json array with each element being the data that is being paged.
     * @param pageSize The number of elements to return with each page
     * @return A [JsonObject] containing the content as a json object. The object will
     * contain the key [pagedArrayKey] that contains all the paged data combined into
     * a single array.
     */
    @Throws(SuiteApiClientException::class)
    @JvmOverloads
    fun getPaged(
        endpoint: String,
        pagedArrayKey: String,
        pageSize: Int = 1000,
    ): JsonObject =
        runBlocking {
            getPagedAsync(endpoint, pagedArrayKey, pageSize)
        }

    /**
     * A Kotlin [suspend] method that performs a paged GET operation on the given endpoint.
     * After the first GET operation succeeds, subsequent GET requests will be done
     * concurrently (with a max of [maxConnections] concurrent requests) until all of
     * paged data has been retrieved.
     * @param endpoint The API endpoint to call
     * @param pagedArrayKey The key on each returned json object to combine. This key should
     * contain a json array with each element being the data that is being paged.
     * @param pageSize The number of elements to return with each page
     * @return A [JsonObject] containing the content as a json object. The object will
     * contain the key [pagedArrayKey] that contains all the paged data combined into
     * a single array.
     */
    @Throws(SuiteApiClientException::class)
    @JvmOverloads
    suspend fun getPagedAsync(
        endpoint: String,
        pagedArrayKey: String,
        pageSize: Int = 1000,
    ): JsonObject {
        val page0 = getAsync(endpoint.addPaging(0, pageSize))
        val total =
            page0["pageInfo"]?.jsonObject?.get("totalCount")?.jsonPrimitive?.int ?: 1
        val remainingPages =
            ceil(((total - pageSize.coerceAtMost(total)).toDouble() / pageSize.toDouble())).roundToInt()

        val elements =
            (listOf(page0) + (
                    (1..remainingPages).asyncMap("Get Paged $endpoint") { page ->
                        getAsync(endpoint.addPaging(page, pageSize))
                    }))
                .flatMap { it[pagedArrayKey]?.jsonArray ?: JsonArray(emptyList()) }

        return JsonObject(
            mapOf(
                "count" to JsonPrimitive(elements.size),
                pagedArrayKey to JsonArray(elements)
            )
        )
    }

    /**
     * A method that performs a POST operation on the given endpoint.
     * @param endpoint The API endpoint to call
     * @param jsonBody A json object containing the payload of the POST request.
     * @return A [JsonObject] containing the content as a json object. Throws if the
     * response code is not 2xx.
     */
    @Throws(SuiteApiClientException::class)
    fun post(endpoint: String, jsonBody: JsonObject): JsonObject =
        runBlocking {
            postAsync(endpoint, jsonBody)
        }

    /**
     * A Kotlin [suspend] method that performs a POST operation on the given endpoint.
     * @param endpoint The API endpoint to call
     * @param jsonBody A json object containing the payload of the POST request.
     * @return A [JsonObject] containing the content as a json object. Throws if the
     * response code is not 2xx.
     */
    @Throws(SuiteApiClientException::class)
    suspend fun postAsync(
        endpoint: String,
        jsonBody: JsonObject,
    ): JsonObject {
        return postRawResponseAsync(endpoint, jsonBody).throwOnErrorStatus().toJson()
    }

    /**
     * A method that performs a POST operation on the given endpoint.
     * @param endpoint The API endpoint to call
     * @param jsonBody A json object containing the payload of the POST request.
     * @return An [HttpResponse] containing the return code and content
     */
    fun postRawResponse(endpoint: String, jsonBody: JsonObject): HttpResponse =
        runBlocking {
            postRawResponseAsync(endpoint, jsonBody)
        }

    /**
     * A Kotlin [suspend] method that performs a POST operation on the given endpoint.
     * @param endpoint The API endpoint to call
     * @param jsonBody A json object containing the payload of the POST request.
     * @return An [HttpResponse] containing the return code and content
     */
    suspend fun postRawResponseAsync(
        endpoint: String,
        jsonBody: JsonObject,
    ): HttpResponse {
        return throttler.throttleCall {
            client.post(connectionInfo.getUrl(endpoint)) {
                accept(ContentType.Application.Json)
                header("Authorization", "vRealizeOpsToken $token")
                if (endpoint.contains("internal")) {
                    logger.debug("Using unsupported API: $endpoint")
                    header("X-vRealizeOps-API-use-unsupported", true)
                }
                contentType(ContentType.Application.Json)
                setBody(jsonBody)
            }
        }
    }

    /**
     * A method that performs a paged POST operation on the given endpoint.
     * After the first GET operation succeeds, subsequent GET requests will be done
     * concurrently (with a max of [maxConnections] concurrent requests) until all the
     * paged data has been retrieved.
     * @param endpoint The API endpoint to call
     * @param pagedArrayKey The key on each returned json object to combine. This key should
     * contain a json array with each element being the data that is being paged.
     * @param pageSize The number of elements to return with each page
     * @return A [JsonObject] containing the content as a json object. The object will
     * contain the key [pagedArrayKey] that contains all the paged data combined into
     * a single array.
     */
    @Throws(SuiteApiClientException::class)
    @JvmOverloads
    fun postPaged(
        endpoint: String,
        jsonBody: JsonObject,
        pagedArrayKey: String,
        pageSize: Int = 1000,
    ): JsonObject =
        runBlocking {
            postPagedAsync(endpoint, jsonBody, pagedArrayKey, pageSize)
        }

    /**
     * A Kotlin [suspend] method that performs a paged POST operation on the given endpoint.
     * After the first GET operation succeeds, subsequent GET requests will be done
     * concurrently (with a max of [maxConnections] concurrent requests) until all the
     * paged data has been retrieved.
     * @param endpoint The API endpoint to call
     * @param pagedArrayKey The key on each returned json object to combine. This key should
     * contain a json array with each element being the data that is being paged.
     * @param pageSize The number of elements to return with each page
     * @return A [JsonObject] containing the content as a json object. The object will
     * contain the key [pagedArrayKey] that contains all the paged data combined into
     * a single array.
     */
    @Throws(SuiteApiClientException::class)
    @JvmOverloads
    suspend fun postPagedAsync(
        endpoint: String,
        jsonBody: JsonObject,
        pagedArrayKey: String,
        pageSize: Int = 1000,
    ): JsonObject {
        val page0 = postAsync(endpoint.addPaging(0, pageSize), jsonBody)
        val total =
            page0["pageInfo"]?.jsonObject?.get("totalCount")?.jsonPrimitive?.int ?: 1
        val remainingPages =
            ceil(((total - pageSize.coerceAtMost(total)).toDouble() / pageSize.toDouble())).roundToInt()

        val elements =
            (listOf(page0) + (
                    (1..remainingPages).asyncMap("Post Paged $endpoint") { page ->
                        postAsync(
                            endpoint.addPaging(page, pageSize),
                            jsonBody
                        )
                    }))
                .flatMap { it[pagedArrayKey]?.jsonArray ?: JsonArray(emptyList()) }

        return JsonObject(
            mapOf(
                "count" to JsonPrimitive(elements.size),
                pagedArrayKey to JsonArray(elements)
            )
        )
    }

    /**
     * A method that performs a DELETE operation on the given endpoint.
     * @param endpoint The API endpoint to call
     */
    @Throws(SuiteApiClientException::class)
    fun delete(endpoint: String) =
        runBlocking {
            deleteAsync(endpoint)
        }

    /**
     * A Kotlin [suspend] method that performs a DELETE operation on the given endpoint.
     * @param endpoint The API endpoint to call
     */
    @Throws(SuiteApiClientException::class)
    suspend fun deleteAsync(endpoint: String) {
        return throttler.throttleCall {
            client.delete(connectionInfo.getUrl(endpoint)) {
                accept(ContentType.Application.Json)
                header("Authorization", "vRealizeOpsToken $token")
                if (endpoint.contains("internal")) {
                    logger.debug("Using unsupported API: $endpoint")
                    header("X-vRealizeOps-API-use-unsupported", true)
                }
            }.throwOnErrorStatus()
        }
    }

    /**
     * Query for resources using the Suite API, and convert the
     * responses to SDK Objects.
     *
     * Note that not all information from the query is returned. For example, the
     * query returns health statuses of each object, but those are not present in
     * the resulting Objects. If information other than the Object itself is needed,
     * you will need to call the endpoint and process the results manually.
     *
     * @param query: json of the resourceQuery, as defined in the SuiteAPI docs:
     * https://[[aria-ops-hostname]]/suite-api/doc/swagger-ui.html#/Resources/getMatchingResourcesUsingPOST
     * @return list of sdk [Objects][Object] representing each of the returned objects.
     */
    fun queryForResources(query: JsonObject): List<Object> {
        try {
            var results = mutableListOf<JsonElement>()
            if (query.containsKey("name") && query.containsKey("regex")) {
                // This is behavior in the suite api itself, we're just warning about it
                // here to avoid confusion.
                logger.warn(
                    "'name' and 'regex' are mutually exclusive in resource " +
                            "queries. Ignoring the 'regex' key in favor of 'name' " +
                            "key."
                )
            }
            // The 'name' key takes an array but only looks up the first element.
            // Fix that limitation here .
            if (query["name"]?.jsonArray?.size?.let { it > 1 } == true) {
                val jsonBody = query
                for (name in query["name"]?.jsonArray ?: emptyList()) {
                    val newJsonBody = jsonBody.toMutableMap()
                    newJsonBody["name"] = buildJsonArray { add(name) }
                    val response = postPaged(
                        "/api/resources/query",
                        Json.encodeToJsonElement(newJsonBody).jsonObject,
                        "resourceList"
                    )
                    results.addAll(
                        response["resourceList"]?.jsonArray ?: buildJsonArray { })
                }
            } else {
                val response = this.postPaged(
                    "/api/resources/query",
                    query,
                    "resourceList",
                )
                results.addAll(
                    response.jsonObject["resourceList"]?.jsonArray ?: buildJsonArray {})
            }
            return results.mapNotNull { obj ->
                obj.jsonObject["resourceKey"]?.jsonObject?.let {
                    keyToObject(it)
                }
            }
        } catch (e: Exception) {
            logger.error(e)
            return emptyList()
        }
    }

    private fun keyToObject(jsonObjectKey: JsonObject): Object? {
        return Object(
            Key(
                jsonObjectKey["adapterKindKey"]?.jsonPrimitive?.content ?: return null,
                jsonObjectKey["resourceKindKey"]?.jsonPrimitive?.content ?: return null,
                jsonObjectKey["name"]?.jsonPrimitive?.content ?: return null,
                jsonObjectKey["resourceIdentifiers"]?.jsonArray?.map { identifier: JsonElement ->
                    Identifier(
                        identifier.jsonObject["identifierType"]?.jsonObject?.get("name")?.jsonPrimitive?.content ?: return null,
                        identifier.jsonObject["value"]?.jsonPrimitive?.content ?: return null,
                        identifier.jsonObject["identifierType"]?.jsonObject?.get("isPartOfUniqueness")?.jsonPrimitive?.booleanOrNull ?: return null,
                    )
                } ?: emptyList()
            )
        )
    }


    /**
     * Releases the token if present and closes any features of the client that require closing
     */
    override fun close() {
        try {
            tokenDelegate.releaseToken()
        } catch (e: SuiteApiClientException) {
            logger.warn("Could not release token. This is likely because the token has already been invalidated. ${e.message}")
            logger.debug(
                "Could not release token. This is likely because the token has already been invalidated. ${e.message}",
                e
            )
        }
        client.close()
    }

    private fun String.addPaging(page: Int = 0, pageSize: Int = 1000): String =
        if (this.contains("?")) {
            "$this&page=$page&pageSize=$pageSize"
        } else {
            "$this?page=$page&pageSize=$pageSize"
        }

    private suspend fun <T> Semaphore.throttleCall(body: suspend () -> T): T {
        this.acquire()
        return try {
            body()
        } finally {
            this.release()
        }
    }
}

private suspend fun HttpResponse.toJson() =
    Json.parseToJsonElement(this.bodyAsText()).jsonObject

private suspend fun HttpResponse.throwOnErrorStatus(): HttpResponse {
    if (this.status.value >= 300) {
        throw SuiteApiClientException(
            "${this.call.request.method.value} request to " +
                    "${this.call.request.url} returned ${this.status.description} " +
                    "(${this.status.value})", this.status.value
        )
    }
    return this
}

private suspend inline fun <T, R> Iterable<T>.asyncMap(
    scopeName: String,
    crossinline transform: suspend CoroutineScope.(T) -> R,
): List<R> {
    val currentScope = CoroutineScope(currentCoroutineContext())
    val context = CoroutineName(scopeName)
    return map { currentScope.async(context) { transform(it) } }.awaitAll()
}
