/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations;

import kotlinx.serialization.json.*;
import org.junit.jupiter.api.*;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

public class TestResultTest {

    @Test
    public void success() {
        TestResult result = new TestResult();
        assertTrue(result.isSuccess());
    }

    @Test
    public void fail() {
        TestResult result = new TestResult();
        result.withError("Failed test");
        assertFalse(result.isSuccess());
    }

    @Test
    public void successJson() {
        TestResult result = new TestResult();
        assertEquals(new JsonObject(new HashMap<>()), result.getJson());
    }

    @Test
    public void failJson() {
        TestResult result = new TestResult();
        result.withError("Failed test");
        JsonObject json = (JsonObject) result.getJson();
        assertEquals("Failed test", ((JsonPrimitive) Objects.requireNonNull(json.get("errorMessage"))).getContent());

    }
}
