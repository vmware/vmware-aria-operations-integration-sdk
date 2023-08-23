/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations;

import kotlinx.serialization.json.*;
import org.junit.jupiter.api.*;

import java.util.*;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class EndpointResultTest {
    @Test
    public void emptyJson() {
        EndpointResult result = new EndpointResult();
        assertEquals(new JsonObject(new HashMap<>()), result.getJson());
    }

    @Test
    public void withEndpoint() {
        EndpointResult result = new EndpointResult();
        result.withEndpoint("endpoint");
        assertEquals(
                new JsonObject(
                        Map.of(
                                "endpointUrls",
                                new JsonArray(List.of(
                                        JsonElementKt.JsonPrimitive("endpoint")
                                ))
                        )
                ),
                result.getJson()
        );
    }

    @Test
    public void withMultipleEndpoint() {
        EndpointResult result = new EndpointResult();
        result.withEndpoint("endpoint");
        result.withEndpoint("endpoint2");
        result.withEndpoint("endpoint3");
        assertEquals(
                new JsonObject(
                        Map.of(
                                "endpointUrls",
                                new JsonArray(List.of(
                                        JsonElementKt.JsonPrimitive("endpoint"),
                                        JsonElementKt.JsonPrimitive("endpoint2"),
                                        JsonElementKt.JsonPrimitive("endpoint3")
                                ))
                        )
                ),
                result.getJson()
        );
    }
}
