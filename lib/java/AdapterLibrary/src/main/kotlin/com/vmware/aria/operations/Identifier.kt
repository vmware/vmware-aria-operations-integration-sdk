/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

import kotlinx.serialization.EncodeDefault
import kotlinx.serialization.EncodeDefault.Mode.ALWAYS
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.Serializable
import java.util.Objects

/**
 * Represents a piece of data that identifies an Object.
 *
 * This class represents a piece of data that identifies an Object. If [isPartOfUniqueness] is false, this data
 * can change over time without creating a new Object. This is primarily used for human-readable values that are
 * useful in identification purposes, but may change at times.
 *
 * @property key A key that determines which identifier the value corresponds to.
 * @property value The value of the identifier.
 * @property isPartOfUniqueness Determines if this key/value pair is used in the identification process.
 */
@Serializable
class Identifier @OptIn(ExperimentalSerializationApi::class)
@JvmOverloads constructor(
    val key: String,
    val value: String,
    @EncodeDefault(ALWAYS) val isPartOfUniqueness: Boolean = true
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
}
