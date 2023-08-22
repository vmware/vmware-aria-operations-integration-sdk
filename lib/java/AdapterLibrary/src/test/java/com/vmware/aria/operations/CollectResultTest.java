/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations;

import kotlinx.serialization.json.JsonObject;
import kotlinx.serialization.json.JsonPrimitive;
import org.junit.jupiter.api.*;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class CollectResultTest {
    Key simpleObjectKey1 = new Key("adapter", "object", "name");
    Key simpleObjectKey2 = new Key("adapter", "object", "name2");
    Key simpleNewObjectKey = new Key("adapter", "newObject", "name3", List.of(new Identifier("key", "value")));
    Key externalKey = new Key("externalAdapter", "object", "name4");

    CollectResult result;
    Object obj1;
    Object obj2;
    Object obj3;
    Object obj4;

    @BeforeEach
    public void setup() {
        result = new CollectResult();
        obj1 = new Object(simpleObjectKey1);
        obj2 = new Object(simpleObjectKey2);
        obj3 = new Object(simpleNewObjectKey);
        obj4 = new Object(externalKey);
    }

    @Test
    public void success() {
        assertTrue(result.isSuccess());
    }

    @Test
    public void fail() {
        result.withError("Failed test");
        assertFalse(result.isSuccess());
    }

    @Test
    public void failJson() {
        result.withError("Failed test");
        JsonObject json = (JsonObject) result.getJson();
        assertEquals("Failed test", ((JsonPrimitive) Objects.requireNonNull(json.get("errorMessage"))).getContent());
    }

    @Test
    public void getOrCreateObject() {
        assertEquals(0, result.getObjects().size());
        Object obj = result.getOrCreateObject(simpleObjectKey1);
        assertEquals(1, result.getObjects().size());
        Object testObj = result.getOrCreateObject(simpleObjectKey1);
        assertEquals(1, result.getObjects().size());
        assertSame(obj, testObj);
    }

    @Test
    public void GetOrCreateObject2() {
        assertEquals(0, result.getObjects().size());
        Object obj = result.getOrCreateObject("adapter", "object", "name");
        assertEquals(1, result.getObjects().size());
        Object testObj = result.getOrCreateObject(simpleObjectKey1);
        assertEquals(1, result.getObjects().size());
        assertSame(obj, testObj);
    }

    @Test
    public void GetOrCreateObject3() {
        assertEquals(0, result.getObjects().size());
        Object obj = result.getOrCreateObject(simpleObjectKey1);
        assertEquals(1, result.getObjects().size());
        Object testObj = result.getOrCreateObject("adapter", "object", "name");
        assertEquals(1, result.getObjects().size());
        assertSame(obj, testObj);
    }

    @Test
    public void GetOrCreateObject4() {
        assertEquals(0, result.getObjects().size());
        Object obj = result.getOrCreateObject("adapter", "newObject", "name3", List.of(new Identifier("key", "value")));
        assertEquals(1, result.getObjects().size());
        Object testObj = result.getOrCreateObject("adapter", "newObject", "name3", List.of(new Identifier("key", "value")));
        assertEquals(1, result.getObjects().size());
        assertSame(obj, testObj);
    }

    @Test
    public void GetOrCreateObject5() {
        assertEquals(0, result.getObjects().size());
        Object obj = result.getOrCreateObject("adapter", "newObject", "name3", List.of(new Identifier("key", "value")));
        assertEquals(1, result.getObjects().size());
        Object testObj = result.getOrCreateObject(simpleNewObjectKey);
        assertEquals(1, result.getObjects().size());
        assertSame(obj, testObj);
    }

    @Test
    public void getObject() {
        assertEquals(0, result.getObjects().size());
        Object obj = result.getObject("adapter", "object", "name");
        assertNull(obj);
        assertEquals(0, result.getObjects().size());
    }

    @Test
    public void getObject2() {
        assertEquals(0, result.getObjects().size());
        Object obj = result.getObject("adapter", "newObject", "name3", List.of(new Identifier("key", "value")));
        assertNull(obj);
        assertEquals(0, result.getObjects().size());
    }

    @Test
    public void getObject3() {
        assertEquals(0, result.getObjects().size());
        Object obj = result.getObject(simpleObjectKey1);
        assertNull(obj);
        assertEquals(0, result.getObjects().size());
    }

    @Test
    public void getObject4() {
        result.addObject(obj1);
        Object testObj = result.getObject("adapter", "object", "name");
        assertSame(obj1, testObj);
    }

    @Test
    public void getObject5() {
        result.addObject(obj3);
        Object testObj = result.getObject("adapter", "newObject", "name3", List.of(new Identifier("key", "value")));
        assertSame(obj3, testObj);
    }

    @Test
    public void getObject6() {
        CollectResult result = new CollectResult();
        result.addObject(obj1);
        Object testObj = result.getObject(simpleObjectKey1);
        assertSame(obj1, testObj);
    }


    @Test
    public void getObjectsByType1() {
        result.addObjects(List.of(obj1, obj2, obj3, obj4));

        List<Object> objects= result.getObjectsByType("object");
        assertEquals(3, objects.size());
        assertTrue(objects.containsAll(List.of(obj1, obj2, obj4)));
    }

    @Test
    public void getObjectsByType2() {
        result.addObjects(List.of(obj1, obj2, obj3, obj4));

        List<Object> objects= result.getObjectsByType("adapter", "object");
        assertEquals(2, objects.size());
        assertTrue(objects.containsAll(List.of(obj1, obj2)));
    }

    @Test
    public void getObjectsByAdapterType() {
        result.addObjects(List.of(obj1, obj2, obj3, obj4));

        List<Object> objects= result.getObjectsByAdapterType("adapter");
        assertEquals(3, objects.size());
        assertTrue(objects.containsAll(List.of(obj1, obj2, obj3)));
    }

    @Test
    public void addObject1() {
        assertEquals(0, result.getObjects().size());
        result.addObject(obj1);
        assertEquals(1, result.getObjects().size());
    }

    @Test
    public void addObject2() {
        assertEquals(0, result.getObjects().size());
        result.addObject(obj1);
        assertEquals(1, result.getObjects().size());
        // Adding the *same* object twice is OK
        result.addObject(obj1);
        assertEquals(1, result.getObjects().size());
    }

    @Test
    public void addObject3() {
        assertEquals(0, result.getObjects().size());
        result.addObject(obj1);
        assertEquals(1, result.getObjects().size());
        assertThrows(ObjectKeyAlreadyExistsException.class, () -> {
            // Adding *different* objects with the same key is not OK
            result.addObject(new Object(obj1.getKey()));
        });
        assertEquals(1, result.getObjects().size());
    }

    @Test
    public void addObjects1() {
        assertEquals(0, result.getObjects().size());
        result.addObjects(List.of(obj1, obj2, obj3, obj4));
        assertEquals(4, result.getObjects().size());
    }

    @Test
    public void addObjects2() {
        assertEquals(0, result.getObjects().size());
        result.addObjects(List.of(obj1, obj4));
        assertEquals(2, result.getObjects().size());
        // Adding the *same* objects twice is OK
        result.addObjects(List.of(obj1, obj2, obj3, obj4));
        assertEquals(4, result.getObjects().size());
    }

    @Test
    public void addObjects3() {
        assertEquals(0, result.getObjects().size());
        result.addObjects(List.of(obj1, obj4));
        assertEquals(2, result.getObjects().size());
        assertThrows(ObjectKeyAlreadyExistsException.class, () -> {
            // Adding *different* objects with the same key is not OK
            result.addObjects(List.of(new Object(obj1.getKey()), obj2, obj3, new Object(obj4.getKey())));
        });
        assertEquals(4, result.getObjects().size());
    }
}
