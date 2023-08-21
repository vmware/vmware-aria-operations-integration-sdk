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
class ObjectKeyAlreadyExistsException(message: String): Exception(message)
