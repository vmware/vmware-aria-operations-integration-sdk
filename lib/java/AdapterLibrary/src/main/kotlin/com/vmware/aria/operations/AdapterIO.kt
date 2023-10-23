/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
@file:JvmName("AdapterIO")

package com.vmware.aria.operations

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import java.io.File
import java.io.FileInputStream
import java.io.InputStreamReader


/**
 * Stores the input and output pipe file names for simplified I/O operations
 */
object Pipes {
    lateinit var input: String
    lateinit var output: String
}

private val logger = getLogger()

/**
 * Reads data from the input pipe.
 *
 * @param inputPipe The path to the input pipe. Defaults to the [Pipes.input] value.
 * @return The data read from the input pipe, or null if there was an error.
 */
@JvmOverloads
fun readFromPipe(inputPipe: String = Pipes.input): JsonElement? {
    try {
        val inputFilePipe = InputStreamReader(FileInputStream(inputPipe))
        logger.debug("Opening $inputPipe")
        val jsonText = inputFilePipe.readText()
        logger.debug("Decoding Json")
        return Json.decodeFromString<JsonElement>(jsonText)
    } catch (e: Exception) {
        logger.error("Error when reading from the Input Pipe.")
        logger.debug(e)
        return null
    }
}

/**
 * Writes data to the output pipe
 * @param result The (json) data to write to the output pipe
 * @param outputPipe The path to the output pipe. Defaults to the [Pipes.output] value.
 */
@JvmOverloads
fun writeToPipe(result: JsonElement, outputPipe: String = Pipes.output) {
    try {
        val outputFilePipe = File(outputPipe)
        logger.debug("Encoding Json")
        val json = Json.encodeToString(result)
        logger.debug("Opening $outputPipe")
        outputFilePipe.writeText(json)
    } catch (e: Exception) {
        logger.error("Error when writing to Output Pipe.")
        logger.debug(e)
    }
    logger.debug("Finished writing results to Output Pipe.")
}