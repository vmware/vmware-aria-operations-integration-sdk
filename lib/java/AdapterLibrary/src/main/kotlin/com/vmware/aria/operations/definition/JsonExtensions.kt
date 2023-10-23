/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations.definition

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonObjectBuilder
import kotlinx.serialization.json.buildJsonObject

internal inline fun extendJsonObject(json: JsonObject, builderAction: JsonObjectBuilder.() -> Unit): JsonObject =
    buildJsonObject {
        json.entries.forEach { entry ->
            put(entry.key, entry.value)
        }
        this.builderAction()
    }
