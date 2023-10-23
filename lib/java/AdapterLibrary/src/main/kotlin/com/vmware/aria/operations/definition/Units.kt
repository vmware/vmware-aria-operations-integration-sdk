/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations.definition

data class SdkUnit(
    val key: String,
    val label: String,
    private val order: Int,
    private val conversionFactor: Int,
    private val subtype: String = "",
    val isRate: Boolean = false,
)

sealed interface UnitGroup {
    val unit: SdkUnit
}

object Units {
    enum class Ratio(override val unit: SdkUnit) : UnitGroup {
        PERCENT(SdkUnit("percent", "%", 1, 1))
    }

    enum class Time(override val unit: SdkUnit) : UnitGroup {
        PICOSECONDS(SdkUnit("picoseconds", "ps", 1, 1)),
        NANOSECONDS(SdkUnit("nanoseconds", "ns", 2, 1000)),
        MICROSECONDS(SdkUnit("microseconds", "μs", 3, 1000)),
        MILLISECONDS(SdkUnit("milliseconds", "ms", 4, 1000)),
        CENTISECONDS(SdkUnit("centiseconds", "cs", 5, 10)),
        SECONDS(SdkUnit("seconds", "s", 6, 100)),
        MINUTES(SdkUnit("minutes", "min", 7, 60)),
        HOURS(SdkUnit("hours", "h", 8, 60)),
        DAYS(SdkUnit("days", "d", 9, 24)),
        WEEKS(SdkUnit("weeks", "wk", 10, 7))  // No ISO Standard for week
    }

    // Some databases use time rates to measure CPU usage, e.g., as CPU Time per Wall Clock Time
    enum class TimeRate(override val unit: SdkUnit) : UnitGroup {
        PICOSECONDS_PER_SEC(
            SdkUnit(
                "picoseconds_per_sec",
                "ps/s",
                1,
                1,
                isRate = true
            )
        ),
        NANOSECONDS_PER_SEC(
            SdkUnit(
                "nanoseconds_per_sec",
                "ns/s",
                2,
                1000,
                isRate = true
            )
        ),
        MICROSECONDS_PER_SEC(
            SdkUnit(
                "microseconds_per_sec",
                "μs/s",
                3,
                1000,
                isRate = true
            )
        ),
        MILLISECONDS_PER_SEC(
            SdkUnit(
                "milliseconds_per_sec",
                "ms/s",
                4,
                1000,
                isRate = true
            )
        ),
        CENTISECONDS_PER_SEC(
            SdkUnit(
                "centiseconds_per_sec",
                "cs/s",
                5,
                10,
                isRate = true
            )
        ),
        SECONDS_PER_SEC(SdkUnit("seconds_per_sec", "s/s", 6, 100, isRate = true)),
        MINUTES_PER_SEC(SdkUnit("minutes_per_sec", "min/s", 7, 60, isRate = true)),
        HOURS_PER_SEC(SdkUnit("hours_per_sec", "h/s", 8, 60, isRate = true)),
        DAYS_PER_SEC(SdkUnit("days_per_sec", "d/s", 9, 24, isRate = true)),
        WEEKS_PER_SEC(SdkUnit("weeks_per_sec", "wk/s", 10, 7, isRate = true)),
    }

    enum class Rate(override val unit: SdkUnit) : UnitGroup {
        PER_PICOSECOND(
            SdkUnit(
                "per_picosecond",
                "per picosecond",
                1,
                1,
                isRate = true
            )
        ),
        PER_NANOSECOND(
            SdkUnit(
                "per_nanosecond",
                "per nanosecond",
                2,
                1000,
                isRate = true
            )
        ),
        PER_MICROSECOND(
            SdkUnit(
                "per_microsecond",
                "per microsecond",
                3,
                1000,
                isRate = true
            )
        ),
        PER_MILLISECOND(
            SdkUnit(
                "per_millisecond",
                "per millisecond",
                4,
                1000,
                isRate = true
            )
        ),
        PER_SECOND(SdkUnit("per_second", "per second", 5, 1000, isRate = true)),
        PER_MINUTE(SdkUnit("per_minute", "per minute", 6, 60, isRate = true)),
        PER_HOUR(SdkUnit("per_hour", "per hour", 7, 60, isRate = true)),
        PER_DAY(SdkUnit("per_day", "per day", 8, 24, isRate = true)),
        PER_WEEK(SdkUnit("per_week", "per week", 9, 7, isRate = true)),
    }

    enum class DataSize(override val unit: SdkUnit) : UnitGroup {
        BIT(SdkUnit("bit", "b", 1, 1)),
        KILOBIT(SdkUnit("kilobit", "kbit", 2, 1000, "bits_base_10")),
        MEGABIT(SdkUnit("megabit", "Mbit", 3, 1000, "bits_base_10")),
        GIGABIT(SdkUnit("gigabit", "Gbit", 4, 1000, "bits_base_10")),
        TERABIT(SdkUnit("terabit", "Tbit", 5, 1000, "bits_base_10")),
        PETABIT(SdkUnit("petabit", "Pbit", 6, 1000, "bits_base_10")),
        EXABIT(SdkUnit("exabit", "Ebit", 7, 1000, "bits_base_10")),
        ZETTABIT(SdkUnit("zettabit", "Zbit", 8, 1000, "bits_base_10")),
        YOTTABIT(SdkUnit("yottabit", "Ybit", 9, 1000, "bits_base_10")),
        BYTE(SdkUnit("byte", "B", 1, 1, "bytes_base_10")),
        KILOBYTE(SdkUnit("kilobyte", "kB", 2, 1000, "bytes_base_10")),
        MEGABYTE(SdkUnit("megabyte", "MB", 3, 1000, "bytes_base_10")),
        GIGABYTE(SdkUnit("gigabyte", "GB", 4, 1000, "bytes_base_10")),
        TERABYTE(SdkUnit("terabyte", "TB", 5, 1000, "bytes_base_10")),
        PETABYTE(SdkUnit("petabyte", "PB", 6, 1000, "bytes_base_10")),
        EXABYTE(SdkUnit("exabyte", "EB", 7, 1000, "bytes_base_10")),
        ZETTABYTE(SdkUnit("zettabyte", "ZB", 8, 1000, "bytes_base_10")),
        YOTTABYTE(SdkUnit("yottabyte", "YB", 9, 1000, "bytes_base_10")),
        BIBIT(SdkUnit("bibit", "b", 1, 1, "bits_base_2")),
        KIBIBIT(SdkUnit("kibibit", "Kibit", 2, 1024, "bits_base_2")),
        MEBIBIT(SdkUnit("mebibit", "Mibit", 3, 1024, "bits_base_2")),
        GIBIBIT(SdkUnit("gibibit", "Gibit", 4, 1024, "bits_base_2")),
        TEBIBIT(SdkUnit("tebibit", "Tibit", 5, 1024, "bits_base_2")),
        PEBIBIT(SdkUnit("pebibit", "Pibit", 6, 1024, "bits_base_2")),
        EXBIBIT(SdkUnit("exbibit", "Eibit", 7, 1024, "bits_base_2")),
        ZEBIBIT(SdkUnit("zebibit", "Zibit", 8, 1024, "bits_base_2")),
        YOBIBIT(SdkUnit("yobibit", "Yibit", 9, 1024, "bits_base_2")),
        BIBYTE(SdkUnit("bibyte", "b", 1, 1, "bytes_base_2")),
        KIBIBYTE(
            SdkUnit(
                "kibibyte", "KiB", 2, 1024, "bytes_base_2"
            )
        ),  // per ISO 80000, this does not follow the convention of lower-case k for kilo
        MEBIBYTE(SdkUnit("mebibyte", "MiB", 3, 1024, "bytes_base_2")),
        GIBIBYTE(SdkUnit("gibibyte", "GiB", 4, 1024, "bytes_base_2")),
        TEBIBYTE(SdkUnit("tebibyte", "TiB", 5, 1024, "bytes_base_2")),
        PEBIBYTE(SdkUnit("pebibyte", "PiB", 6, 1024, "bytes_base_2")),
        EXBIBYTE(SdkUnit("exbibyte", "EiB", 7, 1024, "bytes_base_2")),
        ZEBIBYTE(SdkUnit("zebibyte", "ZiB", 8, 1024, "bytes_base_2")),
        YOBIBYTE(SdkUnit("yobibyte", "YiB", 9, 1024, "bytes_base_2")),
    }

    enum class DataRate(override val unit: SdkUnit) : UnitGroup {
        BIT_PER_SECOND(
            SdkUnit(
                "bitps",
                "bit/s",
                1,
                1,
                "bits_base_10",
                isRate = true
            )
        ),
        KILOBIT_PER_SECOND(
            SdkUnit(
                "kbitps",
                "kbit/s",
                2,
                1000,
                "bits_base_10",
                isRate = true
            )
        ),
        MEGABIT_PER_SECOND(
            SdkUnit(
                "mbitps",
                "Mbit/s",
                3,
                1000,
                "bits_base_10",
                isRate = true
            )
        ),
        GIGABIT_PER_SECOND(
            SdkUnit(
                "gbitps",
                "Gbit/s",
                4,
                1000,
                "bits_base_10",
                isRate = true
            )
        ),
        TERABIT_PER_SECOND(
            SdkUnit(
                "tbitps",
                "Tbit/s",
                5,
                1000,
                "bits_base_10",
                isRate = true
            )
        ),
        PETABIT_PER_SECOND(
            SdkUnit(
                "pbitps",
                "Pbit/s",
                6,
                1000,
                "bits_base_10",
                isRate = true
            )
        ),
        EXABIT_PER_SECOND(
            SdkUnit(
                "ebitps",
                "Ebit/s",
                7,
                1000,
                "bits_base_10",
                isRate = true
            )
        ),
        ZETTABIT_PER_SECOND(
            SdkUnit(
                "zbitps",
                "Zbit/s",
                8,
                1000,
                "bits_base_10",
                isRate = true
            )
        ),
        YOTTABIT_PER_SECOND(
            SdkUnit(
                "ybitps",
                "Ybit/s",
                9,
                1000,
                "bits_base_10",
                isRate = true
            )
        ),
        BYTE_PER_SECOND(
            SdkUnit(
                "byteps",
                "B/s",
                1,
                1,
                "bytes_base_10",
                isRate = true
            )
        ),
        KILOBYTE_PER_SECOND(
            SdkUnit(
                "kbyteps",
                "kB/s",
                2,
                1000,
                "bytes_base_10",
                isRate = true
            )
        ),
        MEGABYTE_PER_SECOND(
            SdkUnit(
                "mbyteps",
                "MB/s",
                3,
                1000,
                "bytes_base_10",
                isRate = true
            )
        ),
        GIGABYTE_PER_SECOND(
            SdkUnit(
                "gbyteps",
                "GB/s",
                4,
                1000,
                "bytes_base_10",
                isRate = true
            )
        ),
        TERABYTE_PER_SECOND(
            SdkUnit(
                "tbyteps",
                "TB/s",
                5,
                1000,
                "bytes_base_10",
                isRate = true
            )
        ),
        PETABYTE_PER_SECOND(
            SdkUnit(
                "pbyteps",
                "PB/s",
                6,
                1000,
                "bytes_base_10",
                isRate = true
            )
        ),
        EXABYTE_PER_SECOND(
            SdkUnit(
                "ebyteps",
                "EB/s",
                7,
                1000,
                "bytes_base_10",
                isRate = true
            )
        ),
        ZETTABYTE_PER_SECOND(
            SdkUnit(
                "zbyteps",
                "ZB/s",
                8,
                1000,
                "bytes_base_10",
                isRate = true
            )
        ),
        YOTTABYTE_PER_SECOND(
            SdkUnit(
                "ybyteps",
                "YB/s",
                9,
                1000,
                "bytes_base_10",
                isRate = true
            )
        ),
        BIBIT_PER_SECOND(
            SdkUnit(
                "bibitps",
                "bit/s",
                1,
                1,
                "bits_base_2",
                isRate = true
            )
        ),
        KIBIBIT_PER_SECOND(
            SdkUnit(
                "kibibitps",
                "kibit/s",
                2,
                1024,
                "bits_base_2",
                isRate = true
            )
        ),
        MEBIBIT_PER_SECOND(
            SdkUnit(
                "mebibitps",
                "Mibit/s",
                3,
                1024,
                "bits_base_2",
                isRate = true
            )
        ),
        GIBIBIT_PER_SECOND(
            SdkUnit(
                "gibibitps",
                "Gibit/s",
                4,
                1024,
                "bits_base_2",
                isRate = true
            )
        ),
        TEBIBIT_PER_SECOND(
            SdkUnit(
                "tebibitps",
                "Tibit/s",
                5,
                1024,
                "bits_base_2",
                isRate = true
            )
        ),
        PEBIBIT_PER_SECOND(
            SdkUnit(
                "pebibitps",
                "Pibit/s",
                6,
                1024,
                "bits_base_2",
                isRate = true
            )
        ),
        EXBIBIT_PER_SECOND(
            SdkUnit(
                "exbibitps",
                "Eibit/s",
                7,
                1024,
                "bits_base_2",
                isRate = true
            )
        ),
        ZEBIBIT_PER_SECOND(
            SdkUnit(
                "zebibitps",
                "Zibit/s",
                8,
                1024,
                "bits_base_2",
                isRate = true
            )
        ),
        YOBIBIT_PER_SECOND(
            SdkUnit(
                "yobibitps",
                "Yibit/s",
                9,
                1024,
                "bits_base_2",
                isRate = true
            )
        ),
        BIBYTE_PER_SECOND(
            SdkUnit(
                "bibyteps",
                "B/s",
                1,
                1,
                "bytes_base_2",
                isRate = true
            )
        ),

        // per ISO 80000, this does not follow the convention of lower-case k for kilo
        KIBIBYTE_PER_SECOND(
            SdkUnit(
                "kibibyteps",
                "KiB/s",
                2,
                1024,
                "bytes_base_2",
                isRate = true
            )
        ),
        MEBIBYTE_PER_SECOND(
            SdkUnit(
                "mebibyteps",
                "MiB/s",
                3,
                1024,
                "bytes_base_2",
                isRate = true
            )
        ),
        GIBIBYTE_PER_SECOND(
            SdkUnit(
                "gibibyteps",
                "GiB/s",
                4,
                1024,
                "bytes_base_2",
                isRate = true
            )
        ),
        TEBIBYTE_PER_SECOND(
            SdkUnit(
                "tebibyteps",
                "TiB/s",
                5,
                1024,
                "bytes_base_2",
                isRate = true
            )
        ),
        PEBIBYTE_PER_SECOND(
            SdkUnit(
                "pebibyteps",
                "PiB/s",
                6,
                1024,
                "bytes_base_2",
                isRate = true
            )
        ),
        EXBIBYTE_PER_SECOND(
            SdkUnit(
                "exbibyteps",
                "EiB/s",
                7,
                1024,
                "bytes_base_2",
                isRate = true
            )
        ),
        ZEBIBYTE_PER_SECOND(
            SdkUnit(
                "zebibyteps",
                "ZiB/s",
                8,
                1024,
                "bytes_base_2",
                isRate = true
            )
        ),
        YOBIBYTE_PER_SECOND(
            SdkUnit(
                "yobibyteps",
                "YiB/s",
                9,
                1024,
                "bytes_base_2",
                isRate = true
            )
        ),
    }

    enum class Frequency(override val unit: SdkUnit) : UnitGroup {
        HERTZ(SdkUnit("hertz", "Hz", 1, 1, isRate = true)),
        KILOHERTZ(SdkUnit("kilohertz", "kHz", 2, 1000, isRate = true)),
        MEGAHERTZ(SdkUnit("megahertz", "MHz", 3, 1000, isRate = true)),
        GIGAHERTZ(SdkUnit("gigahertz", "GHz", 4, 1000, isRate = true)),
        TERAHERTZ(SdkUnit("terahertz", "THz", 5, 1000, isRate = true)),
        PETAHERTZ(SdkUnit("petahertz", "PHz", 6, 1000, isRate = true)),
        EXAHERTZ(SdkUnit("exahertz", "EHz", 7, 1000, isRate = true)),
    }

    enum class Power(override val unit: SdkUnit) : UnitGroup {
        NANOWATT(SdkUnit("nanowatt", "nW", 1, 1, isRate = true)),
        MICROWATT(SdkUnit("microwatt", "μW", 2, 1000, isRate = true)),
        MILLIWATT(SdkUnit("milliwatt", "mW", 3, 1000, isRate = true)),
        WATT(SdkUnit("watt", "W", 4, 1000, isRate = true)),
        KILOWATT(SdkUnit("kilowatt", "kW", 5, 1000, isRate = true)),
        MEGAWATT(SdkUnit("megawatt", "MW", 6, 1000, isRate = true)),
        GIGAWATT(SdkUnit("gigawatt", "GW", 7, 1000, isRate = true)),
        TERAWATT(SdkUnit("terawatt", "TW", 8, 1000, isRate = true)),
    }

    enum class Energy(override val unit: SdkUnit) : UnitGroup {
        NANOWATT_HOURS(SdkUnit("nanowatthours", "nW·h", 1, 1)),
        MICROWATT_HOURS(SdkUnit("microwatthours", "μW·h", 2, 1000)),
        MILLIWATT_HOURS(SdkUnit("milliwatthours", "mW·h", 3, 1000)),
        WATT_HOURS(SdkUnit("watthours", "W·h", 4, 1000)),
        KILOWATT_HOURS(SdkUnit("kilowatthours", "kW·h", 5, 1000)),
        MEGAWATT_HOURS(SdkUnit("megawatthours", "MW·h", 6, 1000)),
        GIGAWATT_HOURS(SdkUnit("gigawatthours", "GW·h", 7, 1000)),
        TERAWATT_HOURS(SdkUnit("terawatthours", "TW·h", 8, 1000)),
    }

    enum class Resistance(override val unit: SdkUnit) : UnitGroup {
        NANOOHM(SdkUnit("nanoohm", "nΩ", 1, 1)),
        MICROOHM(SdkUnit("microohm", "μΩ", 2, 1000)),
        MILLIOHM(SdkUnit("milliohm", "mΩ", 3, 1000)),
        OHM(SdkUnit("ohm", "Ω", 4, 1000)),
        KILOOHM(SdkUnit("kiloohm", "kΩ", 5, 1000)),
        MEGAOHM(SdkUnit("megaohm", "MΩ", 6, 1000)),
        GIGAOHM(SdkUnit("gigaohm", "GΩ", 7, 1000)),
        TERAOHM(SdkUnit("teraohm", "TΩ", 8, 1000)),
    }

    enum class Voltage(override val unit: SdkUnit) : UnitGroup {
        NANOVOLTS(SdkUnit("nanovolts", "nV", 1, 1)),
        MICROVOLTS(SdkUnit("microvolts", "μV", 2, 1000)),
        MILLIVOLTS(SdkUnit("millivolts", "mV", 3, 1000)),
        VOLTS(SdkUnit("volts", "V", 4, 1000)),
        KILOVOLTS(SdkUnit("kilovolts", "kV", 5, 1000)),
        MEGAVOLTS(SdkUnit("megavolts", "MV", 6, 1000)),
        GIGAVOLTS(SdkUnit("gigavolts", "GV", 7, 1000)),
        TERAVOLTS(SdkUnit("teravolts", "TV", 8, 1000)),
    }

    enum class Current(override val unit: SdkUnit) : UnitGroup {
        NANOAMPS(SdkUnit("nanoamps", "nA", 1, 1)),
        MICROAMPS(SdkUnit("microamps", "μA", 2, 1000)),
        MILLIAMPS(SdkUnit("milliamps", "mA", 3, 1000)),
        AMPS(SdkUnit("amps", "A", 4, 1000)),
        KILOAMPS(SdkUnit("kiloamps", "kA", 5, 1000)),
        MEGAAMPS(SdkUnit("megaamps", "MA", 6, 1000)),
        GIGAAMPS(SdkUnit("gigaamps", "GA", 7, 1000)),
        TERAAMPS(SdkUnit("teraamps", "TA", 8, 1000)),
    }

    enum class Charge(override val unit: SdkUnit) : UnitGroup {
        NANOAMP_HOURS(SdkUnit("nanoamphours", "nA·h", 1, 1)),
        MICROAMP_HOURS(SdkUnit("microamphours", "μA·h", 2, 1000)),
        MILLIAMP_HOURS(SdkUnit("milliamphours", "mA·h", 3, 1000)),
        AMP_HOURS(SdkUnit("amphours", "A·h", 4, 1000)),
        KILOAMP_HOURS(SdkUnit("kiloamphours", "kA·h", 5, 1000)),
        MEGAAMP_HOURS(SdkUnit("megaamphours", "MA·h", 6, 1000)),
        GIGAAMP_HOURS(SdkUnit("gigaamphours", "GA·h", 7, 1000)),
        TERAAMP_HOURS(SdkUnit("teraamphours", "TA·h", 8, 1000)),
    }

    enum class Temperature(override val unit: SdkUnit) : UnitGroup {
        C(SdkUnit("celcius", "°C", 1, 1, "celcius")),
        K(SdkUnit("kelvin", "K", 1, 1, "kelvin")),
        F(SdkUnit("fahrenheit", "°F", 1, 1, "fahrenheit")),
    }

    // Note: According to SI, 'rpm' is not a unit
    enum class RotationRate(override val unit: SdkUnit) : UnitGroup {
        RPM(SdkUnit("rpm", "rpm", 1, 1, isRate = true)),
    }


    enum class Misc(override val unit: SdkUnit) : UnitGroup {
        CORES(SdkUnit("cores", "cores", 1, 1, "Cores")),
        MILLICORES(SdkUnit("millicores", "millicores", 1, 1, "Millicores")),
        BLOCKS(SdkUnit("blocks", "blocks", 1, 1, "Blocks")),
        BLOCKS_PER_SECOND(
            SdkUnit(
                "blocksps",
                "blocks/s",
                1,
                1,
                "BlocksPerSecond",
                isRate = true
            )
        ),
        PAGES(SdkUnit("pages", "pages", 1, 1, "Pages")),
        PAGES_PER_SECOND(
            SdkUnit(
                "pagesps",
                "pages/s",
                1,
                1,
                "PagesPerSecond",
                isRate = true
            )
        ),
        PACKETS(SdkUnit("packets", "packets", 1, 1, "Packets")),
        PACKETS_PER_SECOND(
            SdkUnit(
                "packetsps",
                "packets/s",
                1,
                1,
                "PacketsPerSecond",
                isRate = true
            )
        ),
        FRAMES(SdkUnit("frames", "frames", 1, 1, "Frames")),
        FRAMES_PER_SECOND(
            SdkUnit(
                "framesps",
                "frames/s",
                1,
                1,
                "FramesPerSecond",
                isRate = true
            )
        ),
        OPERATIONS(SdkUnit("operations", "operations", 1, 1, "Operations")),
        OPERATIONS_PER_SECOND(
            SdkUnit(
                "operationsps",
                "operations/s",
                1,
                1,
                "OperationsPerSecond",
                isRate = true
            )
        ),
        IO_OPERATIONS_PER_SECOND(SdkUnit("iops", "IOPS", 1, 1, "IOPS")),
        REQUESTS(SdkUnit("requests", "requests", 1, 1, "Requests")),
        REQUESTS_PER_SECOND(
            SdkUnit(
                "requestsps",
                "requests/s",
                1,
                1,
                "RequestsPerSecond",
                isRate = true
            )
        ),
        CALLS(SdkUnit("calls", "calls", 1, 1, "Calls")),
        CALLS_PER_SECOND(
            SdkUnit(
                "callsps",
                "calls/s",
                1,
                1,
                "CallsPerSecond",
                isRate = true
            )
        ),
        ERRORS(SdkUnit("errors", "errors", 1, 1, "Errors")),
        ERRORS_PER_SECOND(
            SdkUnit(
                "errorsps",
                "errors/s",
                1,
                1,
                "ErrorsPerSecond",
                isRate = true
            )
        ),
        FLOPS(SdkUnit("flops", "flops", 1, 1, "FLOPS", isRate = true)),
        KILOFLOPS(
            SdkUnit(
                "kiloflops",
                "kiloflops",
                2,
                1000,
                "FLOPS",
                isRate = true
            )
        ),
        MEGAFLOPS(
            SdkUnit(
                "megaflops",
                "megaflops",
                3,
                1000,
                "FLOPS",
                isRate = true
            )
        ),
        GIGAFLOPS(
            SdkUnit(
                "gigaflops",
                "gigaflops",
                4,
                1000,
                "FLOPS",
                isRate = true
            )
        ),
        TERAFLOPS(
            SdkUnit(
                "teraflops",
                "teraflops",
                5,
                1000,
                "FLOPS",
                isRate = true
            )
        ),
        PETAFLOPS(
            SdkUnit(
                "petaflops",
                "petaflops",
                6,
                1000,
                "FLOPS",
                isRate = true
            )
        ),
        EXAFLOPS(SdkUnit("exaflops", "exaflops", 7, 1000, "FLOPS", isRate = true)),
        RACK_UNIT(SdkUnit("rackunit", "rack unit", 1, 1, "RackUnits")),
        SESSIONS(SdkUnit("sessions", "sessions", 1, 1, "Sessions")),
        CONNECTIONS(SdkUnit("connections", "connections", 1, 1, "Connections")),
        CONNECTIONS_PER_SECOND(
            SdkUnit(
                "connectionsps",
                "connections/s",
                1,
                1,
                "ConnectionsPerSecond",
                isRate = true
            )
        ),
        DISKS(SdkUnit("disks", "disks", 1, 1, "Disks")),
        PURGES(SdkUnit("purges", "purges", 1, 1, "Purges")),
        PURGES_PER_SECOND(
            SdkUnit(
                "purgesps",
                "purges/s",
                1,
                1,
                "PurgesPerSecond",
                isRate = true
            )
        ),
        READS(SdkUnit("reads", "reads", 1, 1, "Reads")),
        READS_PER_SECOND(
            SdkUnit(
                "readsps",
                "reads/s",
                1,
                1,
                "ReadsPerSecond",
                isRate = true
            )
        ),
        SEARCHES(SdkUnit("searches", "searches", 1, 1, "Searches")),
        SEARCHES_PER_SECOND(
            SdkUnit(
                "searchesps",
                "searches/s",
                1,
                1,
                "SearchesPerSecond",
                isRate = true
            )
        ),
        SLOTS(SdkUnit("slots", "slots", 1, 1, "Slots")),
        SLOTS_PER_SECOND(
            SdkUnit(
                "slotsps",
                "slots/s",
                1,
                1,
                "SlotsPerSecond",
                isRate = true
            )
        ),
        THREADS(SdkUnit("threads", "threads", 1, 1, "Threads")),
        WAITS(SdkUnit("waits", "waits", 1, 1, "Waits")),
        WAITS_PER_SECOND(
            SdkUnit(
                "waitsps",
                "waits/s",
                1,
                1,
                "WaitsPerSecond",
                isRate = true
            )
        ),
        WRITES(SdkUnit("writes", "writes", 1, 1, "Writes")),
        WRITES_PER_SECOND(
            SdkUnit(
                "writesps",
                "writes/s",
                1,
                1,
                "WritesPerSecond",
                isRate = true
            )
        ),
        ATTEMPTS(SdkUnit("attempts", "attempts", 1, 1, "Attempts")),
        ATTEMPTS_PER_SECOND(
            SdkUnit(
                "attemptsps",
                "attempts/s",
                1,
                1,
                "AttemptsPerSecond",
                isRate = true
            )
        ),
        BATCHES(SdkUnit("batches", "batches", 1, 1, "Batches")),
        BATCHES_PER_SECOND(
            SdkUnit(
                "batchesps",
                "batches/s",
                1,
                1,
                "BatchesPerSecond",
                isRate = true
            )
        ),
        INDEXES(SdkUnit("indexes", "indexes", 1, 1, "Indexes")),
        INDEXES_PER_SECOND(
            SdkUnit(
                "indexesps",
                "indexes/s",
                1,
                1,
                "IndexesPerSecond",
                isRate = true
            )
        ),
        LOCKS(SdkUnit("locks", "locks", 1, 1, "Locks")),
        LOCKS_PER_SECOND(
            SdkUnit(
                "locksps",
                "locks/s",
                1,
                1,
                "LocksPerSecond",
                isRate = true
            )
        ),
        MERGES(SdkUnit("merges", "merges", 1, 1, "Merges")),
        MERGES_PER_SECOND(
            SdkUnit(
                "mergesps",
                "merges/s",
                1,
                1,
                "MergesPerSecond",
                isRate = true
            )
        ),
        CHECKPOINTS(SdkUnit("checkpoints", "checkpoints", 1, 1, "Checkpoints")),
        CHECKPOINTS_PER_SECOND(
            SdkUnit(
                "checkpointsps",
                "checkpoints/s",
                1,
                1,
                "CheckpointsPerSecond",
                isRate = true
            )
        ),
        ROWS(SdkUnit("rows", "rows", 1, 1, "Rows")),
        ROWS_PER_SECOND(
            SdkUnit(
                "rowsps",
                "rows/s",
                1,
                1,
                "RowsPerSecond",
                isRate = true
            )
        ),
        TABLES(SdkUnit("tables", "tables", 1, 1, "Tables")),
        TRANSACTIONS(SdkUnit("transactions", "transactions", 1, 1, "Transactions")),
        TRANSACTIONS_PER_SECOND(
            SdkUnit(
                "transactionsps",
                "transactions/s",
                1,
                1,
                "TransactionsPerSecond",
                isRate = true
            )
        ),
    }


    val None = SdkUnit("NONE", "", 0, 1)
}
