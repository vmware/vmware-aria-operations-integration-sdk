#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from aenum import Enum
from aenum import skip


# All units should be standardized to ISO 80000 (International System of Quantities) abbreviations.
# If a metric's unit is bits or bytes, but should use the base-2 paths, set the unit to bibit or bibyte, respectively
# "per X" should be spelled out, with 'per X' all lowercase and spelled out
# "Y per X" should be "y/x", with X and Y both abbreviated (if possible)
# non-ISO units should be abbreviated, if a common english abbreviation exists (e.g., week->wk)
# Units that are not common units (e.g., blocks) should be lower case and spelled out


@dataclass
class Unit:
    key: str
    label: str
    _order: int
    _conversion_factor: int
    _subtype: str = ""
    is_rate: bool = False


class UnitGroup(Enum):
    pass


@skip
class Ratio(UnitGroup):
    PERCENT = Unit("percent", "%", 1, 1)


@skip
class Time(UnitGroup):
    PICOSECONDS = Unit("picoseconds", "ps", 1, 1)
    NANOSECONDS = Unit("nanoseconds", "ns", 2, 1000)
    MICROSECONDS = Unit("microseconds", "μs", 3, 1000)
    MILLISECONDS = Unit("milliseconds", "ms", 4, 1000)
    CENTISECONDS = Unit("centiseconds", "cs", 5, 10)
    SECONDS = Unit("seconds", "s", 6, 100)
    MINUTES = Unit("minutes", "min", 7, 60)
    HOURS = Unit("hours", "h", 8, 60)
    DAYS = Unit("days", "d", 9, 24)
    WEEKS = Unit("weeks", "wk", 10, 7)  # No ISO Standard for week


# Some databases use time rates to measure CPU usage, e.g., as CPU Time per Wall Clock Time
@skip
class TimeRate(UnitGroup):
    PICOSECONDS_PER_SEC = Unit("picoseconds_per_sec", "ps/s", 1, 1, is_rate=True)
    NANOSECONDS_PER_SEC = Unit("nanoseconds_per_sec", "ns/s", 2, 1000, is_rate=True)
    MICROSECONDS_PER_SEC = Unit("microseconds_per_sec", "μs/s", 3, 1000, is_rate=True)
    MILLISECONDS_PER_SEC = Unit("milliseconds_per_sec", "ms/s", 4, 1000, is_rate=True)
    CENTISECONDS_PER_SEC = Unit("centiseconds_per_sec", "cs/s", 5, 10, is_rate=True)
    SECONDS_PER_SEC = Unit("seconds_per_sec", "s/s", 6, 100, is_rate=True)
    MINUTES_PER_SEC = Unit("minutes_per_sec", "min/s", 7, 60, is_rate=True)
    HOURS_PER_SEC = Unit("hours_per_sec", "h/s", 8, 60, is_rate=True)
    DAYS_PER_SEC = Unit("days_per_sec", "d/s", 9, 24, is_rate=True)
    WEEKS_PER_SEC = Unit("weeks_per_sec", "wk/s", 10, 7, is_rate=True)


@skip
class Rate(UnitGroup):
    PER_PICOSECOND = Unit("per_picosecond", "per picosecond", 1, 1, is_rate=True)
    PER_NANOSECOND = Unit("per_nanosecond", "per nanosecond", 2, 1000, is_rate=True)
    PER_MICROSECOND = Unit("per_microsecond", "per microsecond", 3, 1000, is_rate=True)
    PER_MILLISECOND = Unit("per_millisecond", "per millisecond", 4, 1000, is_rate=True)
    PER_SECOND = Unit("per_second", "per second", 5, 1000, is_rate=True)
    PER_MINUTE = Unit("per_minute", "per minute", 6, 60, is_rate=True)
    PER_HOUR = Unit("per_hour", "per hour", 7, 60, is_rate=True)
    PER_DAY = Unit("per_day", "per day", 8, 24, is_rate=True)
    PER_WEEK = Unit("per_week", "per week", 9, 7, is_rate=True)


@skip
class DataSize(UnitGroup):
    BIT = Unit("bit", "b", 1, 1)
    KILOBIT = Unit("kilobit", "kbit", 2, 1000, "bits_base_10")
    MEGABIT = Unit("megabit", "Mbit", 3, 1000, "bits_base_10")
    GIGABIT = Unit("gigabit", "Gbit", 4, 1000, "bits_base_10")
    TERABIT = Unit("terabit", "Tbit", 5, 1000, "bits_base_10")
    PETABIT = Unit("petabit", "Pbit", 6, 1000, "bits_base_10")
    EXABIT = Unit("exabit", "Ebit", 7, 1000, "bits_base_10")
    ZETTABIT = Unit("zettabit", "Zbit", 8, 1000, "bits_base_10")
    YOTTABIT = Unit("yottabit", "Ybit", 9, 1000, "bits_base_10")
    BYTE = Unit("byte", "B", 1, 1, "bytes_base_10")
    KILOBYTE = Unit("kilobyte", "kB", 2, 1000, "bytes_base_10")
    MEGABYTE = Unit("megabyte", "MB", 3, 1000, "bytes_base_10")
    GIGABYTE = Unit("gigabyte", "GB", 4, 1000, "bytes_base_10")
    TERABYTE = Unit("terabyte", "TB", 5, 1000, "bytes_base_10")
    PETABYTE = Unit("petabyte", "PB", 6, 1000, "bytes_base_10")
    EXABYTE = Unit("exabyte", "EB", 7, 1000, "bytes_base_10")
    ZETTABYTE = Unit("zettabyte", "ZB", 8, 1000, "bytes_base_10")
    YOTTABYTE = Unit("yottabyte", "YB", 9, 1000, "bytes_base_10")
    BIBIT = Unit("bibit", "b", 1, 1, "bits_base_2")
    KIBIBIT = Unit("kibibit", "Kibit", 2, 1024, "bits_base_2")
    MEBIBIT = Unit("mebibit", "Mibit", 3, 1024, "bits_base_2")
    GIBIBIT = Unit("gibibit", "Gibit", 4, 1024, "bits_base_2")
    TEBIBIT = Unit("tebibit", "Tibit", 5, 1024, "bits_base_2")
    PEBIBIT = Unit("pebibit", "Pibit", 6, 1024, "bits_base_2")
    EXBIBIT = Unit("exbibit", "Eibit", 7, 1024, "bits_base_2")
    ZEBIBIT = Unit("zebibit", "Zibit", 8, 1024, "bits_base_2")
    YOBIBIT = Unit("yobibit", "Yibit", 9, 1024, "bits_base_2")
    BIBYTE = Unit("bibyte", "b", 1, 1, "bytes_base_2")
    KIBIBYTE = Unit(
        "kibibyte", "KiB", 2, 1024, "bytes_base_2"
    )  # per ISO 80000, this does not follow the convention of lower-case k for kilo
    MEBIBYTE = Unit("mebibyte", "MiB", 3, 1024, "bytes_base_2")
    GIBIBYTE = Unit("gibibyte", "GiB", 4, 1024, "bytes_base_2")
    TEBIBYTE = Unit("tebibyte", "TiB", 5, 1024, "bytes_base_2")
    PEBIBYTE = Unit("pebibyte", "PiB", 6, 1024, "bytes_base_2")
    EXBIBYTE = Unit("exbibyte", "EiB", 7, 1024, "bytes_base_2")
    ZEBIBYTE = Unit("zebibyte", "ZiB", 8, 1024, "bytes_base_2")
    YOBIBYTE = Unit("yobibyte", "YiB", 9, 1024, "bytes_base_2")


@skip
class DataRate(UnitGroup):
    BIT_PER_SECOND = Unit("bitps", "bit/s", 1, 1, "bits_base_10", is_rate=True)
    KILOBIT_PER_SECOND = Unit("kbitps", "kbit/s", 2, 1000, "bits_base_10", is_rate=True)
    MEGABIT_PER_SECOND = Unit("mbitps", "Mbit/s", 3, 1000, "bits_base_10", is_rate=True)
    GIGABIT_PER_SECOND = Unit("gbitps", "Gbit/s", 4, 1000, "bits_base_10", is_rate=True)
    TERABIT_PER_SECOND = Unit("tbitps", "Tbit/s", 5, 1000, "bits_base_10", is_rate=True)
    PETABIT_PER_SECOND = Unit("pbitps", "Pbit/s", 6, 1000, "bits_base_10", is_rate=True)
    EXABIT_PER_SECOND = Unit("ebitps", "Ebit/s", 7, 1000, "bits_base_10", is_rate=True)
    ZETTABIT_PER_SECOND = Unit(
        "zbitps", "Zbit/s", 8, 1000, "bits_base_10", is_rate=True
    )
    YOTTABIT_PER_SECOND = Unit(
        "ybitps", "Ybit/s", 9, 1000, "bits_base_10", is_rate=True
    )
    BYTE_PER_SECOND = Unit("byteps", "B/s", 1, 1, "bytes_base_10", is_rate=True)
    KILOBYTE_PER_SECOND = Unit(
        "kbyteps", "kB/s", 2, 1000, "bytes_base_10", is_rate=True
    )
    MEGABYTE_PER_SECOND = Unit(
        "mbyteps", "MB/s", 3, 1000, "bytes_base_10", is_rate=True
    )
    GIGABYTE_PER_SECOND = Unit(
        "gbyteps", "GB/s", 4, 1000, "bytes_base_10", is_rate=True
    )
    TERABYTE_PER_SECOND = Unit(
        "tbyteps", "TB/s", 5, 1000, "bytes_base_10", is_rate=True
    )
    PETABYTE_PER_SECOND = Unit(
        "pbyteps", "PB/s", 6, 1000, "bytes_base_10", is_rate=True
    )
    EXABYTE_PER_SECOND = Unit("ebyteps", "EB/s", 7, 1000, "bytes_base_10", is_rate=True)
    ZETTABYTE_PER_SECOND = Unit(
        "zbyteps", "ZB/s", 8, 1000, "bytes_base_10", is_rate=True
    )
    YOTTABYTE_PER_SECOND = Unit(
        "ybyteps", "YB/s", 9, 1000, "bytes_base_10", is_rate=True
    )
    BIBIT_PER_SECOND = Unit("bibitps", "bit/s", 1, 1, "bits_base_2", is_rate=True)
    KIBIBIT_PER_SECOND = Unit(
        "kibibitps", "kibit/s", 2, 1024, "bits_base_2", is_rate=True
    )
    MEBIBIT_PER_SECOND = Unit(
        "mebibitps", "Mibit/s", 3, 1024, "bits_base_2", is_rate=True
    )
    GIBIBIT_PER_SECOND = Unit(
        "gibibitps", "Gibit/s", 4, 1024, "bits_base_2", is_rate=True
    )
    TEBIBIT_PER_SECOND = Unit(
        "tebibitps", "Tibit/s", 5, 1024, "bits_base_2", is_rate=True
    )
    PEBIBIT_PER_SECOND = Unit(
        "pebibitps", "Pibit/s", 6, 1024, "bits_base_2", is_rate=True
    )
    EXBIBIT_PER_SECOND = Unit(
        "exbibitps", "Eibit/s", 7, 1024, "bits_base_2", is_rate=True
    )
    ZEBIBIT_PER_SECOND = Unit(
        "zebibitps", "Zibit/s", 8, 1024, "bits_base_2", is_rate=True
    )
    YOBIBIT_PER_SECOND = Unit(
        "yobibitps", "Yibit/s", 9, 1024, "bits_base_2", is_rate=True
    )
    BIBYTE_PER_SECOND = Unit("bibyteps", "B/s", 1, 1, "bytes_base_2", is_rate=True)
    KIBIBYTE_PER_SECOND = Unit(
        "kibibyteps", "KiB/s", 2, 1024, "bytes_base_2", is_rate=True
    )  # per ISO 80000, this does not follow the convention of lower-case k for kilo
    MEBIBYTE_PER_SECOND = Unit(
        "mebibyteps", "MiB/s", 3, 1024, "bytes_base_2", is_rate=True
    )
    GIBIBYTE_PER_SECOND = Unit(
        "gibibyteps", "GiB/s", 4, 1024, "bytes_base_2", is_rate=True
    )
    TEBIBYTE_PER_SECOND = Unit(
        "tebibyteps", "TiB/s", 5, 1024, "bytes_base_2", is_rate=True
    )
    PEBIBYTE_PER_SECOND = Unit(
        "pebibyteps", "PiB/s", 6, 1024, "bytes_base_2", is_rate=True
    )
    EXBIBYTE_PER_SECOND = Unit(
        "exbibyteps", "EiB/s", 7, 1024, "bytes_base_2", is_rate=True
    )
    ZEBIBYTE_PER_SECOND = Unit(
        "zebibyteps", "ZiB/s", 8, 1024, "bytes_base_2", is_rate=True
    )
    YOBIBYTE_PER_SECOND = Unit(
        "yobibyteps", "YiB/s", 9, 1024, "bytes_base_2", is_rate=True
    )


@skip
class Frequency(UnitGroup):
    HERTZ = Unit("hertz", "Hz", 1, 1, is_rate=True)
    KILOHERTZ = Unit("kilohertz", "kHz", 2, 1000, is_rate=True)
    MEGAHERTZ = Unit("megahertz", "MHz", 3, 1000, is_rate=True)
    GIGAHERTZ = Unit("gigahertz", "GHz", 4, 1000, is_rate=True)
    TERAHERTZ = Unit("terahertz", "THz", 5, 1000, is_rate=True)
    PETAHERTZ = Unit("petahertz", "PHz", 6, 1000, is_rate=True)
    EXAHERTZ = Unit("exahertz", "EHz", 7, 1000, is_rate=True)


@skip
class Power(UnitGroup):
    NANOWATT = Unit("nanowatt", "nW", 1, 1, is_rate=True)
    MICROWATT = Unit("microwatt", "μW", 2, 1000, is_rate=True)
    MILLIWATT = Unit("milliwatt", "mW", 3, 1000, is_rate=True)
    WATT = Unit("watt", "W", 4, 1000, is_rate=True)
    KILOWATT = Unit("kilowatt", "kW", 5, 1000, is_rate=True)
    MEGAWATT = Unit("megawatt", "MW", 6, 1000, is_rate=True)
    GIGAWATT = Unit("gigawatt", "GW", 7, 1000, is_rate=True)
    TERAWATT = Unit("terawatt", "TW", 8, 1000, is_rate=True)


@skip
class Energy(UnitGroup):
    NANOWATT_HOURS = Unit("nanowatthours", "nW·h", 1, 1)
    MICROWATT_HOURS = Unit("microwatthours", "μW·h", 2, 1000)
    MILLIWATT_HOURS = Unit("milliwatthours", "mW·h", 3, 1000)
    WATT_HOURS = Unit("watthours", "W·h", 4, 1000)
    KILOWATT_HOURS = Unit("kilowatthours", "kW·h", 5, 1000)
    MEGAWATT_HOURS = Unit("megawatthours", "MW·h", 6, 1000)
    GIGAWATT_HOURS = Unit("gigawatthours", "GW·h", 7, 1000)
    TERAWATT_HOURS = Unit("terawatthours", "TW·h", 8, 1000)


@skip
class Resistance(UnitGroup):
    NANOOHM = Unit("nanoohm", "nΩ", 1, 1)
    MICROOHM = Unit("microohm", "μΩ", 2, 1000)
    MILLIOHM = Unit("milliohm", "mΩ", 3, 1000)
    OHM = Unit("ohm", "Ω", 4, 1000)
    KILOOHM = Unit("kiloohm", "kΩ", 5, 1000)
    MEGAOHM = Unit("megaohm", "MΩ", 6, 1000)
    GIGAOHM = Unit("gigaohm", "GΩ", 7, 1000)
    TERAOHM = Unit("teraohm", "TΩ", 8, 1000)


@skip
class Voltage(UnitGroup):
    NANOVOLTS = Unit("nanovolts", "nV", 1, 1)
    MICROVOLTS = Unit("microvolts", "μV", 2, 1000)
    MILLIVOLTS = Unit("millivolts", "mV", 3, 1000)
    VOLTS = Unit("volts", "V", 4, 1000)
    KILOVOLTS = Unit("kilovolts", "kV", 5, 1000)
    MEGAVOLTS = Unit("megavolts", "MV", 6, 1000)
    GIGAVOLTS = Unit("gigavolts", "GV", 7, 1000)
    TERAVOLTS = Unit("teravolts", "TV", 8, 1000)


@skip
class Current(UnitGroup):
    NANOAMPS = Unit("nanoamps", "nA", 1, 1)
    MICROAMPS = Unit("microamps", "μA", 2, 1000)
    MILLIAMPS = Unit("milliamps", "mA", 3, 1000)
    AMPS = Unit("amps", "A", 4, 1000)
    KILOAMPS = Unit("kiloamps", "kA", 5, 1000)
    MEGAAMPS = Unit("megaamps", "MA", 6, 1000)
    GIGAAMPS = Unit("gigaamps", "GA", 7, 1000)
    TERAAMPS = Unit("teraamps", "TA", 8, 1000)


@skip
class Charge(UnitGroup):
    NANOAMP_HOURS = Unit("nanoamphours", "nA·h", 1, 1)
    MICROAMP_HOURS = Unit("microamphours", "μA·h", 2, 1000)
    MILLIAMP_HOURS = Unit("milliamphours", "mA·h", 3, 1000)
    AMP_HOURS = Unit("amphours", "A·h", 4, 1000)
    KILOAMP_HOURS = Unit("kiloamphours", "kA·h", 5, 1000)
    MEGAAMP_HOURS = Unit("megaamphours", "MA·h", 6, 1000)
    GIGAAMP_HOURS = Unit("gigaamphours", "GA·h", 7, 1000)
    TERAAMP_HOURS = Unit("teraamphours", "TA·h", 8, 1000)


@skip
class Temperature(UnitGroup):
    C = Unit("celcius", "°C", 1, 1, "celcius")
    K = Unit("kelvin", "K", 1, 1, "kelvin")
    F = Unit("fahrenheit", "°F", 1, 1, "fahrenheit")


# Note: According to SI, 'rpm' is not a unit
@skip
class RotationRate(UnitGroup):
    RPM = Unit("rpm", "rpm", 1, 1, is_rate=True)


@skip
class Misc(UnitGroup):
    BLOCKS = Unit("blocks", "blocks", 1, 1, "Blocks")
    BLOCKS_PER_SECOND = Unit(
        "blocksps", "blocks/s", 1, 1, "BlocksPerSecond", is_rate=True
    )
    PAGES = Unit("pages", "pages", 1, 1, "Pages")
    PAGES_PER_SECOND = Unit("pagesps", "pages/s", 1, 1, "PagesPerSecond", is_rate=True)
    PACKETS = Unit("packets", "packets", 1, 1, "Packets")
    PACKETS_PER_SECOND = Unit(
        "packetsps", "packets/s", 1, 1, "PacketsPerSecond", is_rate=True
    )
    FRAMES = Unit("frames", "frames", 1, 1, "Frames")
    FRAMES_PER_SECOND = Unit(
        "framesps", "frames/s", 1, 1, "FramesPerSecond", is_rate=True
    )
    OPERATIONS = Unit("operations", "operations", 1, 1, "Operations")
    OPERATIONS_PER_SECOND = Unit(
        "operationsps", "operations/s", 1, 1, "OperationsPerSecond", is_rate=True
    )
    IO_OPERATIONS_PER_SECOND = Unit("iops", "IOPS", 1, 1, "IOPS")
    REQUESTS = Unit("requests", "requests", 1, 1, "Requests")
    REQUESTS_PER_SECOND = Unit(
        "requestsps", "requests/s", 1, 1, "RequestsPerSecond", is_rate=True
    )
    CALLS = Unit("calls", "calls", 1, 1, "Calls")
    CALLS_PER_SECOND = Unit("callsps", "calls/s", 1, 1, "CallsPerSecond", is_rate=True)
    ERRORS = Unit("errors", "errors", 1, 1, "Errors")
    ERRORS_PER_SECOND = Unit(
        "errorsps", "errors/s", 1, 1, "ErrorsPerSecond", is_rate=True
    )
    FLOPS = Unit("flops", "flops", 1, 1, "FLOPS", is_rate=True)
    KILOFLOPS = Unit("kiloflops", "kiloflops", 2, 1000, "FLOPS", is_rate=True)
    MEGAFLOPS = Unit("megaflops", "megaflops", 3, 1000, "FLOPS", is_rate=True)
    GIGAFLOPS = Unit("gigaflops", "gigaflops", 4, 1000, "FLOPS", is_rate=True)
    TERAFLOPS = Unit("teraflops", "teraflops", 5, 1000, "FLOPS", is_rate=True)
    PETAFLOPS = Unit("petaflops", "petaflops", 6, 1000, "FLOPS", is_rate=True)
    EXAFLOPS = Unit("exaflops", "exaflops", 7, 1000, "FLOPS", is_rate=True)
    RACK_UNIT = Unit("rackunit", "rack unit", 1, 1, "RackUnits")
    SESSIONS = Unit("sessions", "sessions", 1, 1, "Sessions")
    CONNECTIONS = Unit("connections", "connections", 1, 1, "Connections")
    CONNECTIONS_PER_SECOND = Unit(
        "connectionsps", "connections/s", 1, 1, "ConnectionsPerSecond", is_rate=True
    )
    DISKS = Unit("disks", "disks", 1, 1, "Disks")
    PURGES = Unit("purges", "purges", 1, 1, "Purges")
    PURGES_PER_SECOND = Unit(
        "purgesps", "purges/s", 1, 1, "PurgesPerSecond", is_rate=True
    )
    READS = Unit("reads", "reads", 1, 1, "Reads")
    READS_PER_SECOND = Unit("readsps", "reads/s", 1, 1, "ReadsPerSecond", is_rate=True)
    SEARCHES = Unit("searches", "searches", 1, 1, "Searches")
    SEARCHES_PER_SECOND = Unit(
        "searchesps", "searches/s", 1, 1, "SearchesPerSecond", is_rate=True
    )
    SLOTS = Unit("slots", "slots", 1, 1, "Slots")
    SLOTS_PER_SECOND = Unit("slotsps", "slots/s", 1, 1, "SlotsPerSecond", is_rate=True)
    THREADS = Unit("threads", "threads", 1, 1, "Threads")
    WAITS = Unit("waits", "waits", 1, 1, "Waits")
    WAITS_PER_SECOND = Unit("waitsps", "waits/s", 1, 1, "WaitsPerSecond", is_rate=True)
    WRITES = Unit("writes", "writes", 1, 1, "Writes")
    WRITES_PER_SECOND = Unit(
        "writesps", "writes/s", 1, 1, "WritesPerSecond", is_rate=True
    )
    ATTEMPTS = Unit("attempts", "attempts", 1, 1, "Attempts")
    ATTEMPTS_PER_SECOND = Unit(
        "attemptsps", "attempts/s", 1, 1, "AttemptsPerSecond", is_rate=True
    )
    BATCHES = Unit("batches", "batches", 1, 1, "Batches")
    BATCHES_PER_SECOND = Unit(
        "batchesps", "batches/s", 1, 1, "BatchesPerSecond", is_rate=True
    )
    INDEXES = Unit("indexes", "indexes", 1, 1, "Indexes")
    INDEXES_PER_SECOND = Unit(
        "indexesps", "indexes/s", 1, 1, "IndexesPerSecond", is_rate=True
    )
    LOCKS = Unit("locks", "locks", 1, 1, "Locks")
    LOCKS_PER_SECOND = Unit("locksps", "locks/s", 1, 1, "LocksPerSecond", is_rate=True)
    MERGES = Unit("merges", "merges", 1, 1, "Merges")
    MERGES_PER_SECOND = Unit(
        "mergesps", "merges/s", 1, 1, "MergesPerSecond", is_rate=True
    )
    CHECKPOINTS = Unit("checkpoints", "checkpoints", 1, 1, "Checkpoints")
    CHECKPOINTS_PER_SECOND = Unit(
        "checkpointsps", "checkpoints/s", 1, 1, "CheckpointsPerSecond", is_rate=True
    )
    ROWS = Unit("rows", "rows", 1, 1, "Rows")
    ROWS_PER_SECOND = Unit("rowsps", "rows/s", 1, 1, "RowsPerSecond", is_rate=True)
    TABLES = Unit("tables", "tables", 1, 1, "Tables")
    TRANSACTIONS = Unit("transactions", "transactions", 1, 1, "Transactions")
    TRANSACTIONS_PER_SECOND = Unit(
        "transactionsps", "transactions/s", 1, 1, "TransactionsPerSecond", is_rate=True
    )


class Units(Enum):
    RATIO = Ratio
    TIME = Time
    TIME_RATE = TimeRate
    RATE = Rate
    DATA_SIZE = DataSize
    DATA_RATE = DataRate
    FREQUENCY = Frequency
    POWER = Power
    ENERGY = Energy
    RESISTANCE = Resistance
    VOLTAGE = Voltage
    CURRENT = Current
    CHARGE = Charge
    TEMPERATURE = Temperature
    ROTATION_RATE = RotationRate
    MISC = Misc
