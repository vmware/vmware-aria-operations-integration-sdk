/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.vmware.aria.operations;

import org.junit.jupiter.api.*;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

public class KeyKtTest {
    @Test
    public void test_get_identifier() {
        List<Identifier> identifiers = Arrays.asList(
            new Identifier("key1", "value1"),
            new Identifier("key2", "value2")
        );
        Key key = new Key("adapter_kind", "object_kind", "name", identifiers);
        assertEquals("value1", key.getIdentifier("key1"));
    }


    @Test
    public void test_get_identifier_with_default() {
        List<Identifier> identifiers = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        Key key = new Key("adapter_kind", "object_kind", "name", identifiers);
        assertEquals("value2", key.getIdentifier("key2", "default"));
    }


    @Test
    public void test_get_not_existing_identifier() {
        List<Identifier> identifiers = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        Key key = new Key("adapter_kind", "object_kind", "name", identifiers);
        assertNull(key.getIdentifier("bad_key"));
    }


    @Test
    public void test_get_not_existing_identifier_with_default() {
        List<Identifier> identifiers = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        Key key = new Key("adapter_kind", "object_kind", "name", identifiers);
        assertEquals("default", key.getIdentifier("bad_key", "default"));
    }


    @Test
    public void test_get_empty_identifier() {
        List<Identifier> identifiers = Arrays.asList(
                new Identifier("key1", ""),
                new Identifier("key2", "value2")
        );
        Key key = new Key("adapter_kind", "object_kind", "name", identifiers);
        assertEquals("", key.getIdentifier("key1"));
    }


    @Test
    public void test_get_empty_identifier_with_default() {
        List<Identifier> identifiers = Arrays.asList(
                new Identifier("key1", ""),
                new Identifier("key2", "value2")
        );
        Key key = new Key("adapter_kind", "object_kind", "name", identifiers);
        assertEquals("default", key.getIdentifier("key1", "default"));
    }

    @Test
    public void test_key_equality() {
        List<Identifier> identifiers1 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        List<Identifier> identifiers2 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        Key key1 = new Key("adapter_kind", "object_kind", "name", identifiers1);
        Key key2 = new Key("adapter_kind", "object_kind", "name", identifiers2);
        assertEquals(key1, key2);
    }

    @Test
    public void test_key_inequality_adapter_kind() {
        List<Identifier> identifiers1 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        List<Identifier> identifiers2 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        Key key1 = new Key("adapter_kind1", "object_kind", "name", identifiers1);
        Key key2 = new Key("adapter_kind2", "object_kind", "name", identifiers2);
        assertNotEquals(key1, key2);
    }

    @Test
    public void test_key_inequality_object_kind() {
        List<Identifier> identifiers1 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        List<Identifier> identifiers2 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        Key key1 = new Key("adapter_kind", "object_kind1", "name", identifiers1);
        Key key2 = new Key("adapter_kind", "object_kind2", "name", identifiers2);
        assertNotEquals(key1, key2);
    }

    @Test
    public void test_key_inequality_identifiers() {
        List<Identifier> identifiers1 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        List<Identifier> identifiers2 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value3")
        );
        Key key1 = new Key("adapter_kind", "object_kind1", "name", identifiers1);
        Key key2 = new Key("adapter_kind", "object_kind2", "name", identifiers2);
        assertNotEquals(key1, key2);
    }

    @Test
    public void test_key_equality_different_names() {
        List<Identifier> identifiers1 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        List<Identifier> identifiers2 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2")
        );
        Key key1 = new Key("adapter_kind", "object_kind", "name1", identifiers1);
        Key key2 = new Key("adapter_kind", "object_kind", "name2", identifiers2);
        assertEquals(key1, key2);
    }

    @Test
    public void test_key_inequality_different_names() {
        List<Identifier> identifiers1 = Arrays.asList(
                new Identifier("key1", "value1", false),
                new Identifier("key2", "value2", false)
        );
        List<Identifier> identifiers2 = Arrays.asList(
                new Identifier("key1", "value1", false),
                new Identifier("key2", "value2", false)
        );
        Key key1 = new Key("adapter_kind", "object_kind", "name1", identifiers1);
        Key key2 = new Key("adapter_kind", "object_kind", "name2", identifiers2);
        assertNotEquals(key1, key2);
    }

    @Test
    public void test_key_equality_different_non_unique_identifiers() {
        List<Identifier> identifiers1 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value2", false)
        );
        List<Identifier> identifiers2 = Arrays.asList(
                new Identifier("key1", "value1"),
                new Identifier("key2", "value3", false)
        );
        Key key1 = new Key("adapter_kind", "object_kind", "name", identifiers1);
        Key key2 = new Key("adapter_kind", "object_kind", "name", identifiers2);
        assertEquals(key1, key2);
    }

}
