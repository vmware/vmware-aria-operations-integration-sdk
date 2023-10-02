/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations.definition

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonObjectBuilder
import kotlinx.serialization.json.addJsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray

sealed class Parameter {
    abstract val key: String
    abstract val label: String
    abstract val description: String?
    abstract val default: Any?
    abstract val required: Boolean
    abstract val advanced: Boolean
    abstract val displayOrder: Int
    abstract val type: String
    open val enum: Boolean = false

    open val json: JsonObject
        get() = buildJsonObject {
            put("key", key)
            put("label", label)
            put("description", description)
            put("default", default?.toString())
            put("required", required)
            put("ident_type", if (advanced) 2 else 1)
            put("display_order", displayOrder)
            put("type", type)
            put("enum", enum)
        }
}

/**
 * @param key Used to identify the parameter.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param description More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
 * @param default The default value of the parameter.
 * @param required True if user is required to provide this parameter. Defaults to True.
 * @param advanced True if the parameter should be collapsed by default. Defaults to False.
 * @param displayOrder Determines the order parameters will be displayed in the UI.
 */
class IntParameter @JvmOverloads constructor(
    override val key: String,
    override val label: String = key,
    override val description: String? = null,
    override val default: Int? = null,
    override val required: Boolean = true,
    override val advanced: Boolean = false,
    override val displayOrder: Int = 0,
) : Parameter() {
    override val type = "integer"
}

/**
 * @param key Used to identify the parameter.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param description More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
 * @param default The default value of the parameter.
 * @param maxLength The max length of the parameter value, Defaults to 512.
 * @param required True if user is required to provide this parameter. Defaults to True.
 * @param advanced True if the parameter should be collapsed by default. Defaults to False.
 * @param displayOrder Determines the order parameters will be displayed in the UI.
 */
class StringParameter @JvmOverloads constructor(
    override val key: String,
    override val label: String = key,
    override val description: String? = null,
    override val default: String? = null,
    val maxLength: Int = 512,
    override val required: Boolean = true,
    override val advanced: Boolean = false,
    override val displayOrder: Int = 0,
) : Parameter() {
    override val type = "string"

    override val json: JsonObject
        get() = appendToJsonObject(super.json) {
            put("max_length", maxLength)
        }
}

/**
 * @param key Used to identify the parameter.
 * @param values An array containing all enum values. If [default] is specified and not part of the array,
 * it will be added as an additional enum value.
 * @param label Label that is displayed in the VMware Aria Operations UI. Defaults to the key.
 * @param description More in-depth explanation of the parameter. Displayed as a tooltip in the VMware Aria Operations UI.
 * @param default The default value of the parameter.
 * @param required True if user is required to provide this parameter. Defaults to True.
 * @param advanced True if the parameter should be collapsed by default. Defaults to False.
 * @param displayOrder Determines the order parameters will be displayed in the UI.
 */
class EnumParameter @JvmOverloads constructor(
    override val key: String,
    val values: List<EnumValue>,
    override val label: String = key,
    override val description: String? = null,
    override val default: String? = null,
    override val required: Boolean = true,
    override val advanced: Boolean = false,
    override val displayOrder: Int = 0,
) : Parameter() {
    override val type = "string"
    override val enum = true

    data class EnumValue @JvmOverloads constructor(val key: String, val label: String = key)

    override val json: JsonObject
        get() = appendToJsonObject(super.json) {
            putJsonArray("enum_values") {
                val allValues = values.toMutableList()
                default?.let { default ->
                    if (allValues.firstOrNull { it.key == default } == null) {
                        allValues.add(0, EnumValue(default, default))
                    }
                }
                allValues.mapIndexed { index, enum ->
                    addJsonObject {
                        put("key", enum.key)
                        put("label", enum.label)
                        put("display_order", index)
                    }
                }
            }
        }
}

private fun appendToJsonObject(
    initial: JsonObject,
    builderAction: JsonObjectBuilder.() -> Unit,
) =
    buildJsonObject {
        initial.entries.forEach {
            put(it.key, it.value)
        }
        builderAction()
    }