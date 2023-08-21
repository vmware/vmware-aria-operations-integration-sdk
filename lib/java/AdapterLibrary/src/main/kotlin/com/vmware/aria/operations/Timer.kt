/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
@file:JvmName("Timing")

package com.vmware.aria.operations

import com.vmware.aria.operations.Timer.Companion.timers
import kotlin.math.roundToInt
import kotlin.time.ComparableTimeMark
import kotlin.time.Duration
import kotlin.time.DurationUnit
import kotlin.time.TimeSource


/**
 * Creates and starts a new timer. The timer will run until [stop] is called.
 * Timers are automatically registered and can be graphed in aggregate using the [graph] method.
 * @property name A name to identify the timer.
 */
class Timer constructor(val name: String) {
    internal val startTime: ComparableTimeMark
    internal var endTime: ComparableTimeMark? = null
    internal val duration: Duration
        get() = endTime?.let { it - startTime } ?: Duration.INFINITE

    init {
        startTime = TimeSource.Monotonic.markNow()
        timers.add(this)
    }

    /**
     * Stops the timer. Once stopped, a timer cannot be restarted.
     */
    fun stop() {
        if (endTime == null) {
            endTime = TimeSource.Monotonic.markNow()
        }
    }

    /**
     * Gets the duration of the timer in milliseconds
     */
    fun getDuration(): Long =
        duration.inWholeMilliseconds

    /**
     * @return The timer's name and duration. If the timer has not been stopped, the duration
     * will read as 'Infinity'
     */
    override fun toString(): String =
        "$name: ${duration.toTime()}"

    companion object {
        internal val timers: MutableList<Timer> = mutableListOf()

    }
}

/**
 * Times the function / closure. The time is not returned but can be graphed using the
 * [graph] function.
 *
 * @param name The name for this timer
 * @param fn The function or closure to time
 * @return The result of [fn]
 */
fun <T> time(name: String, fn: () -> T?): T? {
    val timer = Timer(name)
    val returnValue = fn()
    timer.stop()
    return returnValue
}

private enum class LineStyle(val horizontalChar: String, val junctionChar: String) {
    UPPER("━", "┯"),
    MIDDLE("━", "┿"),
    LOWER("━", "┷"),
}

/**
 * Graphs all the [Timers][Timer] that have been started since program start, or the last
 * invocation of [clearTimers].
 */
fun graph(): String {
    val width = 88
    val sortedTimers = timers.sortedBy { timer -> timer.startTime }
    val timeMin = sortedTimers.first().startTime
    val timeMax =
        timers.maxOf { timer -> timer.endTime ?: TimeSource.Monotonic.markNow() }
    val nameMax = timers.maxOf { timer -> timer.name.length }
    val graphWidth = width - nameMax - 10
    val duration = timeMax - timeMin
    val headers = listOf(
        "Operation".padEnd(nameMax),
        "Time".padEnd(8),
        "t=0s".padEnd(graphWidth / 2) +
                "t=${duration.toTime()}".padStart((graphWidth + 1) / 2)
    )
    val graph = StringBuilder()
    graph.appendLine("Timing Graph: ")
    graph.appendLine(horizontalLine(headers, LineStyle.UPPER))
    graph.appendLine(headers.joinToString("│"))
    graph.appendLine(horizontalLine(headers, LineStyle.MIDDLE))
    for (timer in sortedTimers) {
        graph.appendLine(display(timer, timeMin, timeMax, headers))
    }
    graph.appendLine(horizontalLine(headers, LineStyle.LOWER))
    return graph.toString()
}

/**
 * Clears all currently running and stopped timers. Use this to start a new timing graph.
 */
fun clearTimers() {
    timers.clear()
}

private fun horizontalLine(headers: List<String>, style: LineStyle): String =
    headers.joinToString("") { header ->
        style.horizontalChar.repeat(header.length) + style.junctionChar
    }.dropLast(1)

private fun display(
    timer: Timer,
    startTime: ComparableTimeMark,
    endTime: ComparableTimeMark,
    headers: List<String>,
): String =
    listOf(
        timer.name.padEnd(headers[0].length),
        timer.duration.toTime().padEnd(headers[1].length),
        graphTimer(timer, startTime, endTime, headers[2].length)
    ).joinToString("│")

private fun graphTimer(
    timer: Timer,
    startTime: ComparableTimeMark,
    endTime: ComparableTimeMark,
    width: Int,
): String {
    val step = (endTime - startTime).div(width - 1)
    val start = (timer.startTime - startTime).div(step).roundToInt()
    val end = ((timer.endTime ?: endTime) - startTime).div(step).roundToInt()
    var line = "".padEnd(start)
    if (start == end) {
        line += "━"
    } else {
        line += "╾"
        line += "─".repeat(end - start - 1)
        line += timer.endTime?.let { "╼" } ?: "─"
    }
    return line
}

private fun Duration.toTime(): String {
    val seconds = toDouble(DurationUnit.SECONDS)
    if (seconds >= 3600)
        return toString(DurationUnit.HOURS, 2)
    else if (seconds > 120)
        return toString(DurationUnit.MINUTES, 2)
    return toString(DurationUnit.SECONDS, 2)
}
