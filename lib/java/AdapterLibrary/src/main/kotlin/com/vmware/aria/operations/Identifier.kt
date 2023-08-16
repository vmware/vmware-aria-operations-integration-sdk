/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

import java.util.Objects

/**
 * Represents a piece of data that identifies an Object.
 *
 * This class represents a piece of data that identifies an Object. If [isPartOfUniqueness] is false, this data
 * can change over time without creating a new Object. This is primarily used for human-readable values that are
 * useful in identification purposes, but may change at times.
 *
 * @param key A key that determines which identifier the value corresponds to.
 * @param value The value of the identifier.
 * @param isPartOfUniqueness Determines if this key/value pair is used in the identification process.
 */
class Identifier @JvmOverloads constructor(
    val key: String,
    val value: String,
    val isPartOfUniqueness: Boolean = true
) {
    override fun toString(): String {
        val uniqueness = if (isPartOfUniqueness) "*" else ""
        return "$key$uniqueness:$value"
    }

    @Throws(IdentifierUniquenessException::class)
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other == null || javaClass != other.javaClass) return false
        val that = other as Identifier
        if (key == that.key) {
            if (isPartOfUniqueness != that.isPartOfUniqueness) {
                throw IdentifierUniquenessException(
                    "Identifier $key has an inconsistent uniqueness attribute"
                )
            }
            return if (isPartOfUniqueness) {
                value == that.value
            } else {
                true
            }
        }
        return false
    }

    override fun hashCode(): Int {
        return if (isPartOfUniqueness) {
            Objects.hash(key, true, value)
        } else {
            Objects.hash(key, false)
        }
    }

    /**
     * Get a JSON representation of this Identifier.
     * This method returns a JSON representation of this Key in the format required by VMware Aria Operations.
     * @return The JSON representation of this Identifier, as a Map
     */
    val json: Map<String, Any>
        get() = mapOf(
            "key" to key,
            "value" to value,
            "isPartOfUniqueness" to isPartOfUniqueness,
        )
}
