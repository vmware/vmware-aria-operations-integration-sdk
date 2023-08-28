package com.vmware.aria.operations;

import kotlinx.serialization.json.*;
import org.junit.jupiter.api.*;

import java.io.*;
import java.nio.file.*;
import java.util.*;

import static org.junit.jupiter.api.Assertions.assertEquals;

class AdapterIOTest {

    static String PATH;
    static String FILE;

    static {
        try {
            PATH = Files.createTempDirectory("JavaAdapterIOTest").toFile().getAbsolutePath();
            FILE = new File(PATH, "fifo.pipe").getAbsolutePath();
            Runtime.getRuntime().exec("mkfifo " + FILE);

            // deleteOnExit deletes in the reverse order they were registered in
            new File(PATH).deleteOnExit();
            new File(FILE).deleteOnExit();

            Pipes.INSTANCE.setInput(FILE);
            Pipes.INSTANCE.setOutput(FILE);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    static JsonElement TEST_JSON = new JsonObject(Map.of(
            "key", JsonElementKt.JsonPrimitive("value"),
            "key2", JsonElementKt.JsonPrimitive(60),
            "array_key", new JsonArray(List.of(
                    JsonElementKt.JsonPrimitive("a"),
                    JsonElementKt.JsonPrimitive("b"),
                    JsonElementKt.JsonPrimitive("c"),
                    new JsonObject(Map.of(
                            "key", JsonElementKt.JsonPrimitive(60),
                            "sub_array_key", new JsonArray(List.of(
                                    JsonElementKt.JsonPrimitive("a"))
                            )))
            ))));

    @Test
    public void writeAndReadFromPipe() throws InterruptedException {
        // Pipes block the writer until the reader starts accessing, and a reader
        // blocks until it has finished reading. We'll use a thread to ensure both can
        // happen without deadlocking.
        WriterThread thread = new WriterThread();
        thread.start();
        JsonElement result = AdapterIO.readFromPipe();
        thread.join();
        assertEquals(TEST_JSON, result);
    }

    public class WriterThread extends Thread {
        public void run() {
            AdapterIO.writeToPipe(TEST_JSON);
        }
    }
}