/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations.adapters.mysqlextension;

import com.vmware.aria.operations.*;
import com.vmware.aria.operations.Object;
import com.vmware.aria.operations.Timer;
import com.vmware.aria.operations.definition.*;
import kotlinx.serialization.json.*;
import org.apache.logging.log4j.Logger;

import java.io.FileNotFoundException;
import java.sql.*;
import java.util.*;

public class Adapter {
    private static final String ADAPTER_KIND = "ExtendedMySQLJavaMP";
    private static final String ADAPTER_NAME = "Extended MySQL MP";

    // These are from the MySQL MP
    private static final String MYSQL_ADAPTER_TYPE = "MySQLAdapter";
    private static final String MYSQL_DATABASE_OBJECT_TYPE = "mysql_database";


    public AdapterDefinition getAdapterDefinition() {
        Timer timer = new Timer("Get Adapter Definition");
        Logger logger = AdapterLogger.getLogger();
        AdapterDefinition definition = null;
        try {
            definition = new AdapterDefinition(ADAPTER_KIND, ADAPTER_NAME);

            definition.defineStringParameter("host", "MySQL Host");
            definition.defineIntegerParameter("port", (parameter) -> {
                parameter.setLabel("Port");
                parameter.setDefault(3306);
            });

            CredentialType credential = definition.defineCredentialType("mysql_user", "MySQL User");
            credential.defineStringParameter("username", "Username");
            credential.definePasswordParameter("password", "Password");

            // The key 'container_memory_limit' is a special key read by the VMware Aria Operations
            // collector to determine how much memory to allocate to the docker container running
            // this adapter. It does not need to be read inside the adapter code. However, removing
            // the definition from the object model will remove the ability to change the container
            // memory limit during the adapter's configuration, and the VMware Aria Operations collector
            // will give 1024 MB of memory to the container running the adapter instance.
            definition.defineIntegerParameter(
                    "container_memory_limit",
                    "Adapter Memory Limit (MB)",
                    "Sets the maximum amount of memory VMware Aria Operations can " +
                            "allocate to the container running this adapter instance.",
                    1024,
                    true,
                    true
            );

            // This Adapter has no object types directly, rather it co-opts object types that
            // are part of the MySQL MP to add additional metrics. As such, we can't define
            // those object types here, because they're already defined in the MySQL MP with a
            // different adapter type.

            // If we decide to also create new objects (that are not part of an existing MP),
            // those can be added here.

            logger.debug("Returning adapter definition:" + definition.getJson());
            return definition;

        } catch (Exception e) {
            logger.error(e.getMessage(), e);
        } finally {
            timer.stop();
        }

        return definition;
    }

    public TestResult test(AdapterInstance adapterInstance) {
        Timer timer = new Timer("Test");
        Logger logger = AdapterLogger.getLogger();
        TestResult result = new TestResult();
        try {
            String hostname = adapterInstance.getIdentifierValue("host");
            Integer port = Integer.valueOf(adapterInstance.getIdentifierValue("port", "3306"));
            String username = adapterInstance.getCredentialValue("username");
            String password = adapterInstance.getCredentialValue("password");

            // Check that we have values for all the identifiers/credentials we need
            if (hostname == null) {
                result.withError("No MySQL Host found");
            }
            if (port == null || port < 1 || port > 65535){
                result.withError("MySQL Port must be an integer from 1-65535");
            }
            if (username == null || password == null) {
                result.withError("No Credential found");
            }

            if (!result.isSuccess()) {
                return result;
            }

            Connection connection = DriverManager.getConnection("jdbc:mysql://" + hostname + ":" + port, username, password);
            Statement statement = connection.createStatement();

            // Run a simple test query
            statement.executeQuery("SHOW databases");

            try(ResultSet rs = statement.getResultSet()) {
                while (rs.next()) {
                    logger.info("Found database '" + rs.getString("database") + "'");
                }
            } catch (SQLException ex) {
                throw new RuntimeException(ex);
            } finally {
                statement.close();
                connection.close();
            }
        } catch (SQLException ex) {
            throw new RuntimeException(ex);
        } catch (Exception e) {
            logger.error("Unexpected connection test error", e);
            result.withError("Unexpected connection test error: " + e.getMessage());
        } finally {
            // TODO: If any connections are still open, make sure they are closed before returning
            logger.debug("Returning test result:" + result.getJson());
            timer.stop();
        }

        return result;
    }

    public CollectResult collect(AdapterInstance adapterInstance) {
        Timer timer = new Timer("Collection");
        Logger logger = AdapterLogger.getLogger();
        CollectResult result = new CollectResult();

        try {
            Timer connectingToMySQL = new Timer("Connecting to MySQL");

            String hostname = adapterInstance.getIdentifierValue("host");
            Integer port = Integer.valueOf(adapterInstance.getIdentifierValue("port", "3306"));
            String username = adapterInstance.getCredentialValue("username");
            String password = adapterInstance.getCredentialValue("password");
            Connection connection = DriverManager.getConnection("jdbc:mysql://" + hostname + ":" + port, username, password);

            connectingToMySQL.stop();
            Timer getDatabaseList = new Timer("Query database list");

            List<JsonElement> databaseNames = new ArrayList<>();
            Statement statement = connection.createStatement();
            statement.executeQuery("SHOW databases");
            try(ResultSet rs = statement.getResultSet()) {
                while (rs.next()) {
                    databaseNames.add(JsonElementKt.JsonPrimitive(hostname + "/" + rs.getString("database")));
                }
            } catch (SQLException ex) {
                throw new RuntimeException(ex);
            } finally {
                statement.close();
            }

            getDatabaseList.stop();
            Timer getSuiteApiDatabases = new Timer("Get database objects from SuiteAPI");

            // Get the list of objects from the SuiteAPI that represent the MySQL
            // databases that are on this instance, and add any we find to the result
            Map<String, Object> databases = new HashMap<>();  // dict of database Objects by name for easy access
            SuiteApiClient suiteApi= adapterInstance.getSuiteApiClient();
            List<Object> dbs= suiteApi.queryForResources(
                    new JsonObject(new HashMap<String, JsonElement>() {{
                            put("adapterKind", new JsonArray(List.of(JsonElementKt.JsonPrimitive(MYSQL_ADAPTER_TYPE))));
                            put("resourceKind", new JsonArray(List.of(JsonElementKt.JsonPrimitive(MYSQL_DATABASE_OBJECT_TYPE))));
                            put("name", new JsonArray(databaseNames));
                        }}));
            for (Object db : dbs) {
                databases.put(db.getIdentifierValue("database_name"), db);
                // Add each database to the collection result.Objects must be
                // added to the result in order for them to be returned by the
                // collect method.
                result.addObject(db);
            }

            getSuiteApiDatabases.stop();
            Timer addLockWaitMetrics = new Timer("Add lock wait metrics");
            // Run a query to get some additional data. Here we're getting info about
            // lock waits on each database
            statement = connection.createStatement();
            statement.executeQuery("""
                    select OBJECT_SCHEMA,
                           sum(COUNT_STAR)     as COUNT_STAR,
                           sum(SUM_TIMER_WAIT) as SUM_TIMER_WAIT,
                           max(MAX_TIMER_WAIT) as MAX_TIMER_WAIT,
                           min(MIN_TIMER_WAIT) as MIN_TIMER_WAIT
                    from performance_schema.table_lock_waits_summary_by_table
                    group by OBJECT_SCHEMA
                    """);

            // Iterate through the results of the query, and add them to the appropriate
            // database Object as metrics.
            try(ResultSet rs = statement.getResultSet()) {
                while (rs.next()) {
                    Object database = databases.get(rs.getString(1));
                    if(database == null) {
                        logger.info("Database " + rs.getString(1) + " not found in Aria Operations");
                        continue;
                    }
                    database.withMetric("Table Locks|Count", rs.getDouble(2));
                    database.withMetric("Table Locks|Sum", rs.getDouble(3));
                    database.withMetric("Table Locks|Max", rs.getDouble(4));
                    if (rs.getDouble(2) > 0) {
                        database.withMetric("Table Locks|Avg", rs.getDouble(3) / rs.getDouble(2));
                    }
                    else {
                        database.withMetric("Table Locks|Avg", 0);
                    }
                    database.withMetric("Table Locks|Min", rs.getDouble(5));
                }
            } catch (SQLException ex) {
                throw new RuntimeException(ex);
            } finally {
                statement.close();
            }

            addLockWaitMetrics.stop();

            connection.close();

            return result;
        } catch (Exception e) {
            logger.error("Unexpected collection error", e);
            result.withError("Unexpected collection error: " + e.getMessage());
        } finally {
            logger.debug("Returning collection result" + result.getJson());
            timer.stop();
        }

        return result;
    }

    public EndpointResult getEndpoints(AdapterInstance adapterInstance) {
        // The MySQL endpoint does not use the HTTPS protocol, so we don't
        // need to return anything here.
        return new EndpointResult();
    }

    // Main entry point of the adapter. You should not need to modify anything below this line.
    public static void main(String[] args) throws FileNotFoundException {
        AdapterLogger.setupLogging("Adapter");
        Logger logger = AdapterLogger.getLogger();

        // Start a new log file by calling 'rotate'. By default, the last five calls will be
        // retained. If the logs are not manually rotated, the 'setup_logging' call should be
        // invoked with the 'max_size' parameter set to a reasonable value, e.g.,
        // 10_489_760 (10MB).
        AdapterLogger.rotate();
        logger.info("Running adapter code with arguments: " + String.join(", ", args));
        if (args.length != 3) {
            // `inputfile` and `outputfile` are always automatically appended to the
            // argument list by the server
            logger.error("Arguments must be <method> <inputfile> <outputfile>");
            System.exit(1);
        }

        String method = args[0];
        try {
            Pipes.input = args[1];
            Pipes.output = args[2];

            Adapter adapter = new Adapter();

            switch (method) {
                case "test":
                    adapter.test(AdapterInstance.fromInput()).sendResults();
                    break;
                case "endpoint_urls":
                    adapter.getEndpoints(AdapterInstance.fromInput()).sendResults();
                    break;
                case "collect":
                    adapter.collect(AdapterInstance.fromInput()).sendResults();
                    break;
                case "adapter_definition":
                    AdapterDefinition result = adapter.getAdapterDefinition();
                    if (result != null) {
                        result.sendResults();
                    } else {
                        logger.info("getAdapterDefinition method did not return an AdapterDefinition");
                        System.exit(1);
                    }
                    break;
                default:
                    logger.error("Command " + method + " not found");
                    System.exit(1);
            }
        } finally {
            logger.info(Timing.graph());
        }
    }
}

