#  Copyright 2022-2023 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0
import sys
from typing import List

import aria.ops.adapter_logging as logging
import mysql.connector
from aria.ops.adapter_instance import AdapterInstance
from aria.ops.definition.adapter_definition import AdapterDefinition
from aria.ops.result import CollectResult
from aria.ops.result import EndpointResult
from aria.ops.result import TestResult
from aria.ops.timer import Timer
from constants import ADAPTER_KIND
from constants import ADAPTER_NAME
from constants import MYSQL_ADAPTER_TYPE
from constants import MYSQL_DATABASE_OBJECT_TYPE

logger = logging.getLogger(__name__)


def test(adapter_instance: AdapterInstance) -> TestResult:
    with Timer(logger, "Test"):
        result = TestResult()
        connection = None
        cursor = None
        try:
            hostname = adapter_instance.get_identifier_value("host")
            port = int(adapter_instance.get_identifier_value("port", "3306"))
            username = adapter_instance.get_credential_value("username")
            password = adapter_instance.get_credential_value("password")

            # Check that we have values for all the identifiers/credentials we need
            if hostname is None:
                result.with_error("No MySQL Host found")
            if type(port) is not int or port < 1 or port > 65535:
                result.with_error("MySQL Port must be an integer from 1-65535")
            if username is None or password is None:
                result.with_error("No Credential found")

            if not result.is_success():
                return result

            connection = mysql.connector.connect(
                host=hostname,
                port=port,
                user=username,
                password=password,
            )
            cursor = connection.cursor()

            # Run a simple test query
            cursor.execute("SHOW databases")

            # The cursor needs to be consumed before it is closed
            for database in cursor:
                logger.info(f"Found database '{database[0]}'")

            logger.debug(f"Returning test result: {result.get_json()}")
            return result
        except Exception as e:
            logger.error("Unexpected connection test error")
            logger.exception(e)
            result.with_error("Unexpected connection test error: " + repr(e))
            return result
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()


def get_endpoints(adapter_instance: AdapterInstance) -> EndpointResult:
    # The MySQL endpoint does not use the HTTPS protocol, so we don't
    # need to return anything here.
    return EndpointResult()


def collect(adapter_instance: AdapterInstance) -> CollectResult:
    with Timer(logger, "Collect"):
        result = CollectResult()
        connection = None
        cursor = None
        try:
            with Timer(logger, "Connecting to MySQL"):
                # Connect to the database, using the same method as test connect
                hostname = adapter_instance.get_identifier_value("host")
                port = int(adapter_instance.get_identifier_value("port", "3306"))
                username = adapter_instance.get_credential_value("username")
                password = adapter_instance.get_credential_value("password")

                connection = mysql.connector.connect(
                    host=hostname,
                    port=port,
                    user=username,
                    password=password,
                )

            with Timer(logger, "Query database list"):
                # Get the list of databases on this instance
                cursor = connection.cursor()
                cursor.execute("SHOW databases")
                database_names = [f"{hostname}/{database[0]}" for database in cursor]
                cursor.close()

            with Timer(logger, "Get database objects from SuiteAPI"):
                # Get the list of objects from the SuiteAPI that represent the MySQL
                # databases that are on this instance, and add any we find to the result
                databases = {}  # dict of database Objects by name for easy access
                with adapter_instance.suite_api_client as suite_api:
                    dbs = suite_api.query_for_resources(
                        query={
                            "adapterKind": [MYSQL_ADAPTER_TYPE],
                            "resourceKind": [MYSQL_DATABASE_OBJECT_TYPE],
                            "name": database_names,
                        },
                    )
                    for db in dbs:
                        databases[db.get_identifier_value("database_name")] = db
                        # Add each database to the collection result. Objects must be
                        # added to the result in order for them to be returned by the
                        # collect method.
                        result.add_object(db)

            with Timer(logger, "Add lock wait metrics"):
                # Run a query to get some additional data. Here we're getting info about
                # lock waits on each database
                cursor = connection.cursor()
                cursor.execute(
                    """
                    select OBJECT_SCHEMA,
                           sum(COUNT_STAR)     as COUNT_STAR,
                           sum(SUM_TIMER_WAIT) as SUM_TIMER_WAIT,
                           max(MAX_TIMER_WAIT) as MAX_TIMER_WAIT,
                           min(MIN_TIMER_WAIT) as MIN_TIMER_WAIT
                    from performance_schema.table_lock_waits_summary_by_table
                    group by OBJECT_SCHEMA
                    """
                )

                # Iterate through the results of the query, and add them to the appropriate
                # database Object as metrics.
                for row in cursor:
                    if len(row) != 5:
                        logger.error(f"Row is not expected size: {repr(row)}")
                        continue
                    database = databases.get(row[0])
                    if not database:
                        logger.info(f"Database {row[0]} not found in Aria Operations")
                        continue
                    database.with_metric("Table Locks|Count", float(row[1]))
                    database.with_metric("Table Locks|Sum", float(row[2]))
                    database.with_metric("Table Locks|Max", float(row[3]))
                    if float(row[1] > 0):
                        database.with_metric(
                            "Table Locks|Avg", float(row[2]) / float(row[1])
                        )
                    else:
                        database.with_metric("Table Locks|Avg", 0)
                    database.with_metric("Table Locks|Min", float(row[4]))
                cursor.close()

            logger.debug(f"Returning collection result {result.get_json()}")
            return result
        except Exception as e:
            logger.error("Unexpected collection error")
            logger.exception(e)
            result.with_error("Unexpected collection error: " + repr(e))
            return result
        finally:
            # If any connections are still open, make sure they are closed before returning
            if cursor:
                cursor.close()
            if connection:
                connection.close()


def get_adapter_definition() -> AdapterDefinition:
    with Timer(logger, "Get Adapter Definition"):
        definition = AdapterDefinition(ADAPTER_KIND, ADAPTER_NAME)

        definition.define_string_parameter("host", "MySQL Host")
        definition.define_int_parameter("port", "Port", default=3306)

        credential = definition.define_credential_type("mysql_user", "MySQL User")
        credential.define_string_parameter("username", "Username")
        credential.define_password_parameter("password", "Password")

        # The key 'container_memory_limit' is a special key that is read by the VMware Aria Operations collector to
        # determine how much memory to allocate to the docker container running this adapter. It does not
        # need to be read inside the adapter code.
        definition.define_int_parameter(
            "container_memory_limit",
            label="Adapter Memory Limit (MB)",
            description="Sets the maximum amount of memory VMware Aria Operations can "
            "allocate to the container running this adapter instance.",
            required=True,
            advanced=True,
            default=1024,
        )

        # This Adapter has no object types directly, rather it co-opts object types that
        # are part of the MySQL MP to add additional metrics. As such, we can't define
        # those object types here, because they're already defined in the MySQL MP with a
        # different adapter type.

        # If we decide to also create new objects (that are not part of an existing MP),
        # those can be added here.

        logger.debug(f"Returning adapter definition: {definition.to_json()}")
        return definition


# Main entry point of the adapter. You should not need to modify anything below this line.
def main(argv: List[str]) -> None:
    logging.setup_logging("adapter.log")
    # Start a new log file by calling 'rotate'. By default, the last five calls will be
    # retained. If the logs are not manually rotated, the 'setup_logging' call should be
    # invoked with the 'max_size' parameter set to a reasonable value, e.g.,
    # 10_489_760 (10MB).
    logging.rotate()
    logger.info(f"Running adapter code with arguments: {argv}")
    if len(argv) != 3:
        # `inputfile` and `outputfile` are always automatically appended to the
        # argument list by the server
        logger.error("Arguments must be <method> <inputfile> <ouputfile>")
        exit(1)

    method = argv[0]

    try:
        if method == "test":
            test(AdapterInstance.from_input()).send_results()
        elif method == "endpoint_urls":
            get_endpoints(AdapterInstance.from_input()).send_results()
        elif method == "collect":
            collect(AdapterInstance.from_input()).send_results()
        elif method == "adapter_definition":
            result = get_adapter_definition()
            if type(result) is AdapterDefinition:
                result.send_results()
            else:
                logger.info(
                    "get_adapter_definition method did not return an AdapterDefinition"
                )
                exit(1)
        else:
            logger.error(f"Command {method} not found")
            exit(1)
    finally:
        logger.info(Timer.graph())


if __name__ == "__main__":
    main(sys.argv[1:])
