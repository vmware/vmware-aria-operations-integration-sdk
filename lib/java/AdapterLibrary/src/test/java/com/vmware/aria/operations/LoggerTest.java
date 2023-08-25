/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations;

import org.apache.logging.log4j.*;
import org.apache.logging.log4j.core.config.*;
import org.junit.jupiter.api.*;

import java.io.*;
import java.nio.file.*;
import java.util.*;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class LoggerTest {
    static String FILENAME = "loggerTest";
    static String PATH;

    static {
        try {
            PATH = Files.createTempDirectory("tmpDirPrefix").toFile().getAbsolutePath();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    ;
    static File CONFIG_FILE = new File(PATH + "/loglevels.cfg");
    static File LOG_0 = new File(PATH + "/" + FILENAME + ".log");
    static File LOG_1 = new File(PATH + "/" + FILENAME + ".log.1");
    static File LOG_2 = new File(PATH + "/" + FILENAME + ".log.2");
    static File LOG_3 = new File(PATH + "/" + FILENAME + ".log.3");

    @AfterEach
    public void reset() {
        // Removes all files in temp directory, rather than just what we are expecting to be present
        List<File> files = Arrays.stream(Objects.requireNonNull(new File(PATH).listFiles())).toList();
        for (File file : files) {
            file.delete();
        }

        // Re-initialize log4j2. Weird things happen if this isn't done (or done
        // incompletely) between tests
        Configurator.initialize(new DefaultConfiguration());
        Configurator.reconfigure();
    }

    @AfterAll
    public static void removeTempDir() {
        new File(PATH).delete();
    }


    @Test
    public void setupLoggingTest() {
        AdapterLogger.setupLogging(FILENAME, 5, 0, PATH);
        Logger logger = AdapterLogger.getLogger();
        logger.debug("setupLoggingTest");
        logger.info("setupLoggingTest");
        logger.warn("setupLoggingTest");
        logger.error("setupLoggingTest");
        logger.fatal("setupLoggingTest");

        // Default level is INFO
        assertFalse(fileContains(LOG_0, "DEBUG"));
        assertTrue(fileContains(LOG_0, "INFO"));
        assertTrue(fileContains(LOG_0, "WARN"));
        assertTrue(fileContains(LOG_0, "ERROR"));
        assertTrue(fileContains(LOG_0, "FATAL"));
    }

    @Test
    public void rotateTest() {
        AdapterLogger.setupLogging(FILENAME, 5, 0, PATH);
        Logger logger = AdapterLogger.getLogger();
        logger.info("rotateTest1");
        AdapterLogger.rotate();
        logger.info("rotateTest2");

        assertTrue(fileContains(LOG_0, "rotateTest2"));
        assertTrue(fileContains(LOG_1, "rotateTest1"));
        assertFalse(LOG_2.exists());
    }

    @Test
    public void rotateMaxBackups() {
        AdapterLogger.setupLogging(FILENAME, 2, 0, PATH);
        Logger logger = AdapterLogger.getLogger();
        logger.info("rotateTest1");
        AdapterLogger.rotate();
        logger.info("rotateTest2");
        AdapterLogger.rotate();
        logger.info("rotateTest3");
        AdapterLogger.rotate();
        logger.info("rotateTest4");

        assertTrue(fileContains(LOG_0, "rotateTest4"));
        assertTrue(fileContains(LOG_1, "rotateTest3"));
        assertTrue(fileContains(LOG_2, "rotateTest2"));
        assertFalse(LOG_3.exists());
    }

    @Test
    public void rotateMaxFileSize() {
        AdapterLogger.setupLogging(FILENAME, 2, 100, PATH);
        Logger logger = AdapterLogger.getLogger();
        String message = "A long message that will reach the max size limit of 100 bytes";
        logger.info(message);
        logger.info(message);
        assertTrue(fileContains(LOG_0, message));
        assertTrue(fileContains(LOG_1, message));
        assertFalse(LOG_2.exists());
    }

    @Test
    public void readConfigTest() {
        PyCFG cfg = new PyCFG();
        cfg.addSection("adapter");
        cfg.set("adapter", "test", Level.FATAL.name());
        cfg.write(CONFIG_FILE);

        AdapterLogger.setupLogging(FILENAME, 5, 0, PATH);
        Logger defaultLogger = AdapterLogger.getLogger();
        Logger testLogger = AdapterLogger.getLogger("test");

        defaultLogger.info("DEFAULT_LOGGER_INFO");
        testLogger.info("TEST_LOGGER_INFO");
        testLogger.fatal("TEST_LOGGER_FATAL");

        assertTrue(fileContains(LOG_0, "DEFAULT_LOGGER_INFO"));
        assertFalse(fileContains(LOG_0, "TEST_LOGGER_INFO"));
        assertTrue(fileContains(LOG_0, "TEST_LOGGER_FATAL"));
    }

    @Test
    public void readConfigTest2() {
        PyCFG cfg = new PyCFG();
        cfg.addSection("adapter");
        // Ensure that we can set to a lower level than the root logger. This can be a
        // problem if the appender log level isn't set correctly.
        cfg.set("adapter", "test", Level.DEBUG.name());
        cfg.write(CONFIG_FILE);

        AdapterLogger.setupLogging(FILENAME, 5, 0, PATH);
        Logger defaultLogger = AdapterLogger.getLogger();
        Logger testLogger = AdapterLogger.getLogger("test");

        defaultLogger.debug("DEFAULT_LOGGER_DEBUG");
        defaultLogger.info("DEFAULT_LOGGER_INFO");
        testLogger.debug("TEST_LOGGER_DEBUG");
        testLogger.info("TEST_LOGGER_INFO");

        assertFalse(fileContains(LOG_0, "DEFAULT_LOGGER_DEBUG"));
        assertTrue(fileContains(LOG_0, "DEFAULT_LOGGER_INFO"));
        assertTrue(fileContains(LOG_0, "TEST_LOGGER_DEBUG"));
        assertTrue(fileContains(LOG_0, "TEST_LOGGER_INFO"));
    }

    public boolean fileContains(File file, String expectedContents) {
        try {
            if (!file.exists()) {
                return false;
            }
            String contents = String.join(System.lineSeparator(), Files.readAllLines(file.toPath()));
            return contents.contains(expectedContents);
        } catch (IOException e) {
            return false;
        }
    }
}
