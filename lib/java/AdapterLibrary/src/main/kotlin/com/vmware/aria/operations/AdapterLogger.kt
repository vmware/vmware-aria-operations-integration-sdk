/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
@file:JvmName("AdapterLogger")

package com.vmware.aria.operations

import org.apache.logging.log4j.Level
import org.apache.logging.log4j.LogManager
import org.apache.logging.log4j.Logger
import org.apache.logging.log4j.core.LoggerContext
import org.apache.logging.log4j.core.appender.RollingFileAppender
import org.apache.logging.log4j.core.appender.rolling.CompositeTriggeringPolicy
import org.apache.logging.log4j.core.appender.rolling.DefaultRolloverStrategy
import org.apache.logging.log4j.core.appender.rolling.OnStartupTriggeringPolicy
import org.apache.logging.log4j.core.appender.rolling.SizeBasedTriggeringPolicy
import org.apache.logging.log4j.core.config.Configurator
import org.apache.logging.log4j.core.layout.PatternLayout
import org.apache.logging.log4j.util.StackLocatorUtil
import java.io.File
import kotlin.io.path.Path


/**
 * Sets up logging using the given parameters
 *
 * @param filename The name of the file to log to.
 * @param backupFileCount The total number of backup files to retain. Defaults to 5.
 * @param maxSize The maximum size in bytes of each file before the file
 *  automatically rotates to a new one. Defaults to '0', which will
 *  do no automatic rotation. May require calling the 'rotate()' function
 *  manually to ensure logs do not become too large.
 */
@JvmOverloads
fun setupLogging(
    filename: String,
    backupFileCount: Int = 5,
    maxSize: Long = 0L,
) {
    // '/var/log' is the location of logs in the Adapter Container, and shouldn't
    // be changed.
    setupLogging(filename, backupFileCount, maxSize, "/var/log")
}

/**
 * Internal constructor for testing purposes that sets up logging using the given parameters
 *
 * @param filename The name of the file to log to.
 * @param backupFileCount The total number of backup files to retain. Defaults to 5.
 * @param maxSize The maximum size in bytes of each file before the file
 *  automatically rotates to a new one. Defaults to '0', which will
 *  do no automatic rotation. Requires calling the 'rotate()' function
 *  manually to ensure logs do not become too large.
 *  @param filePath The location where the config file and logs reside in.
 */
internal fun setupLogging(
    filename: String,
    backupFileCount: Int,
    maxSize: Long,
    filePath: String,
) {

    val pattern = "%d [%t] %-5level: %msg%n%throwable"

    // Trigger a log rollover on startup and if the file exceeds 'maxSize' bytes
    val triggeringPolicy = CompositeTriggeringPolicy.createPolicy(
        OnStartupTriggeringPolicy.createPolicy(1),
        if (maxSize > 0) {
            SizeBasedTriggeringPolicy.createPolicy("$maxSize")
        } else {
            SizeBasedTriggeringPolicy.createPolicy(null)
        }
    )

    val rolloverStrategy = DefaultRolloverStrategy.newBuilder()
        .withMax("$backupFileCount")
        // By default, the rollover strategy counts 'up', so that once the main log file
        // rolls over, it goes to the highest available number and all other backup logs
        // shift down. VMware Aria Ops logs are not set up this way, and neither is
        // Python's logging system. Setting fileIndex to 'min' changes the behavior to
        // match, where when the main log file rolls over, it goes to the minimum number
        // (e.g., *.log.1) and all other backup logs shift up.
        .withFileIndex("min")
        .build()

    val patternLayout = PatternLayout.newBuilder()
        .withPattern(pattern)
        .build()

    val rollingFileAppender = RollingFileAppender.newBuilder()
        .setName("Rolling Adapter File Appender")
        .setLayout(patternLayout)
        .withFileName("$filePath/$filename.log")
        .withFilePattern("$filePath/$filename.log.%i")
        .withPolicy(triggeringPolicy)
        .withStrategy(rolloverStrategy)
        .build()
    rollingFileAppender.start()

    val context = LogManager.getContext(false) as LoggerContext
    val level = getDefaultLogLevel(filePath)
    val filter = context.configuration.rootLogger.filter

    // There are two different levels here - the level of the root logger, and the level
    // of the appender. The level of the root logger is the level that all new loggers
    // will have if they haven't explicitly been overridden. The level of the appender
    // acts as a filter on all loggers that are using the appender. So if the appender
    // is set to INFO, it will never emit a DEBUG log, even if the logger itself
    // is set to DEBUG level. For this reason, we're setting the appender to the 'ALL'
    // level
    context.configuration.rootLogger.level = level
    context.configuration.rootLogger.addAppender(rollingFileAppender, Level.ALL, filter);
    context.configuration.addAppender(rollingFileAppender)
    setLogLevels(filePath)
    context.updateLoggers();
}

/**
 * Returns a Logger with the name of the calling class. This is identical to calling Log4j's
 * LogManager.getLogger() method. It is reimplemented here for convenience.
 *
 * @return The Logger for the calling class.
 * @throws UnsupportedOperationException if the calling class cannot be determined.
 */
fun getLogger(): Logger =
    LogManager.getLogger(StackLocatorUtil.getCallerClass(2))

/**
 * Returns a Logger with the name of the calling class. This is identical to calling Log4j's
 * LogManager.getLogger(name) method. It is reimplemented here for convenience.
 *
 * @param name the name of the Logger.
 * @return The Logger with the given name.
 */
fun getLogger(name: String): Logger =
    LogManager.getLogger(name)

/**
 * Manually trigger the log files to rotate.
 */
fun rotate() {
    val logger = LogManager.getLogger() as org.apache.logging.log4j.core.Logger
    // Iterate through each rolling appender and perform a rollover.
    // 'toSet' is used to ensure we don't roll over any appender twice
    logger.appenders.values.toSet().forEach { appender ->
        if (appender is RollingFileAppender) {
            appender.manager.rollover()
        }
    }
}

private fun getDefaultLogLevel(
    filePath: String,
    defaultLevel: Level = Level.INFO,
): Level {
    val config = PyCFG()
    val configFile = Path(filePath).resolve("loglevels.cfg").toFile()
    config.read(configFile)
    var modified = false
    if (!config.defaults().containsKey("adapter")) {
        modified = true
        config.setDefault("adapter", defaultLevel.name())
    }
    if (!config.hasSection("adapter")) {
        modified = true
        config.addSection("adapter")
        config.set("adapter", "main", defaultLevel.name())
    }
    if (modified) {
        config.write(configFile)
    }
    return try {
        Level.getLevel(
            config.defaults().getOrDefault("adapter", defaultLevel.name())
        )
    } catch (_: IllegalArgumentException) {
        defaultLevel
    }
}

private fun setLogLevels(filePath: String) {
    val config = PyCFG()
    val configFile = Path(filePath).resolve("loglevels.cfg").toFile()
    config.read(configFile)
    config.section("adapter").forEach { (name, level) ->
        Configurator.setLevel(name, level)
    }
}

/**
 * Simple class to read and write Python cfg (ini) files
 */
internal class PyCFG {
    private val config = LinkedHashMap<String, LinkedHashMap<String, String>>()

    fun read(file: File) {
        var currentSection = config.getOrPut(DEFAULT) { LinkedHashMap() }
        if (!file.exists()) {
            return
        }
        file.readLines().map { it.trim() }.forEach { line ->
            if (line.startsWith("[") && line.endsWith("]")) {
                val section = line.drop(1).dropLast(1)
                currentSection = config.getOrPut(section) { LinkedHashMap() }
            } else if (line.startsWith(";") || line.startsWith("#") || line.isBlank()) {
                // comment or empty line; ignore
                return@forEach
            } else if (line.contains("=")) {
                // value
                val key = line.substringBefore("=").trim()
                val value = line.substringAfter("=").trim()
                currentSection[key] = value
            } else {
                // ignore?
            }
        }
    }

    fun write(file: File) {
        if (!file.exists()) {
            file.createNewFile()
        }
        file.printWriter().use { ini ->
            config.forEach { (section, sectionContents) ->
                ini.println("[$section]")
                sectionContents.forEach { (key, value) ->
                    ini.println("$key = $value")
                }
                ini.println()
            }
        }
    }

    fun hasSection(section: String) = config.containsKey(section)
    fun addSection(section: String) {
        config.getOrPut(section) { LinkedHashMap() }
    }

    fun set(section: String, key: String, value: String) {
        config[section]?.set(key, value)
    }

    fun setDefault(key: String, value: String) {
        config[DEFAULT]?.set(key, value)
    }

    fun section(section: String): Map<String, String> = config[section] ?: mapOf()
    fun defaults(): Map<String, String> = config.getOrPut(DEFAULT) { LinkedHashMap() }

    fun get(section: String, key: String, default: String? = null) =
        section(section)[key] ?: defaults()[key] ?: default

    companion object {
        private const val DEFAULT = "DEFAULT"
    }
}