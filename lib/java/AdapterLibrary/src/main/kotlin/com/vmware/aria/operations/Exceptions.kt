/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

/**
 * Exception when two identifiers with the same key have different 'uniqueness' settings
 */
class IdentifierUniquenessException(message: String) : RuntimeException(message)

/**
 * Exception when two objects with the same Key are added to the same CollectResult
 */
class ObjectKeyAlreadyExistsException private constructor(message: String) : Exception(message) {
    constructor(keys: Iterable<Key>) : this(constructMessage(keys))
    constructor(key: Key) : this(constructMessage(listOf(key)))

    companion object {
        fun constructMessage(keys: Iterable<Key>): String =
            if (keys.count() > 1) {
                "Duplicate objects with keys $keys already exist in the CollectResult."
            } else {
                "A duplicate object with key ${keys.first()} already exists in the CollectResult."
            }
    }
}

class SuiteApiClientException(message: String, val responseCode: Int? = null) : Exception(message)

open class KeyException(message: String) : Exception(message)

class DuplicateKeyException(message: String) : KeyException(message)
