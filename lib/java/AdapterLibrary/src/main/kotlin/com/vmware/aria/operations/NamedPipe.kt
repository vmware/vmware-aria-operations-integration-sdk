/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
@file:JvmName("NamedPipe")

package com.vmware.aria.operations

import kotlinx.serialization.json.JsonElement


object Pipes {
    lateinit var input: String
    lateinit var output: String
}

/**
 * Reads data from the input pipe.
 *
 * @param inputPipe The path to the input pipe.
 * @return The data read from the input pipe, or null if there was an error.
 */
fun readFromPipe(inputPipe: String = Pipes.input): JsonElement? {
    // Placeholder for use in *Result classes
    return null
}

/**
 * Writes data to the output pipe
 * @param outputPipe The path to the output pipe
 * @param result The (json) data to write to the output pipe
 */
fun writeToPipe(result: JsonElement, outputPipe: String = Pipes.output) {
    // Placeholder for use in *Result classes
}