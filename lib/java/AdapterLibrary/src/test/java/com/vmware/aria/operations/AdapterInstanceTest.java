package com.vmware.aria.operations;

import kotlinx.serialization.json.*;
import org.junit.jupiter.api.*;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class AdapterInstanceTest {
    private JsonArray arr(List<? extends JsonElement> a) {
        return new JsonArray(a);
    }

    private JsonObject obj(Map<String, ? extends JsonElement> o) {
        return new JsonObject(o);
    }

    private JsonPrimitive str(String s) {
        return JsonElementKt.JsonPrimitive(s);
    }

    private JsonPrimitive bool(boolean b) {
        return JsonElementKt.JsonPrimitive(b);
    }

    private JsonPrimitive n(Number i) {
        return JsonElementKt.JsonPrimitive(i);
    }

    private JsonPrimitive nil() {
        return JsonElementKt.JsonPrimitive((Boolean) null);
    }

    JsonObject KEY = obj(Map.of(
            "name", str("MyAdapterInstanceName"),
            "adapter_kind", str("MyAdapterKind"),
            "object_kind", str("MyAdapterKind_AdapterInstance"),
            "identifiers", arr(List.of(
                    obj(Map.of(
                            "key", str("id1"),
                            "value", str("value1"),
                            "is_part_of_uniqueness", bool(true)
                    )),
                    obj(Map.of(
                            "key", str("id2"),
                            "value", str("value2"),
                            "is_part_of_uniqueness", bool(true)
                    ))
            ))
    ));

    String CREDENTIAL_TYPE = "type1";
    String FIELD1 = "field1";
    String FIELD1_VALUE = "value1";
    String FIELD2 = "field2";
    String FIELD2_VALUE = "value2";
    JsonObject CREDENTIAL = obj(Map.of(
            "credential_key", str(CREDENTIAL_TYPE),
            "credential_fields", arr(List.of(
                    obj(Map.of(
                            "key", str(FIELD1),
                            "value", str(FIELD1_VALUE),
                            "is_password", bool(false)
                    )),
                    obj(Map.of(
                            "key", str(FIELD2),
                            "value", str(FIELD2_VALUE),
                            "is_password", bool(false)
                    ))
            ))
    ));

    JsonObject NULL_CREDENTIAL = obj(Map.of());

    String CERT1 = "Certificate1_ae4c200b34";
    String CERT2 = "Certificate2_ff7d2c2b65";
    JsonElement CERTIFICATES = obj(Map.of(
            "certificates", arr(List.of(
                    str(CERT1),
                    str(CERT2)
            ))
    ));

    String USERNAME = "user1";
    String PASSWORD = "P@SSW0RD";
    String HOSTNAME = "https://host.com";
    JsonElement CLUSTER_CONNECTION_INFO = obj(Map.of(
            "user_name", str(USERNAME),
            "password", str(PASSWORD),
            "host_name", str(HOSTNAME)
    ));

    Double START_TIME = 123.456;
    Double END_TIME = 456.789;
    JsonElement WINDOW = obj(Map.of(
            "start_time", n(START_TIME),
            "end_time", n(END_TIME)
    ));

    Integer COLLECTION_NUMBER = 1;
    JsonObject ADAPTER_INSTANCE1 = obj(Map.of(
            "adapter_key", KEY,
            "credential_config", CREDENTIAL,
            "cluster_connection_info", CLUSTER_CONNECTION_INFO,
            "certificate_config", CERTIFICATES,
            "collection_number", n(COLLECTION_NUMBER),
            "collection_window", WINDOW
    ));
    JsonObject ADAPTER_INSTANCE2 = obj(Map.of(
            "adapter_key", KEY,
            "credential_config", CREDENTIAL,
            "cluster_connection_info", JsonNull.INSTANCE,
            "certificate_config", CERTIFICATES,
            "collection_number", n(COLLECTION_NUMBER),
            "collection_window", WINDOW
    ));

    @Test
    public void getIdentifierValue() {
        AdapterInstance ai = new AdapterInstance(ADAPTER_INSTANCE1);
        System.out.println(ai.getKey());
        assertEquals("value1", ai.getIdentifierValue("id1"));
    }

    @Test
    public void getCredential() {
        AdapterInstance ai = new AdapterInstance(ADAPTER_INSTANCE1);
        assertNotNull(ai.getCredential());
        assertEquals(CREDENTIAL_TYPE, ai.getCredential().getType());
        assertEquals(FIELD1_VALUE, ai.getCredential().get(FIELD1));
        assertEquals(FIELD2_VALUE, ai.getCredential().get(FIELD2));
        assertNull(ai.getCredential().get("field3"));
    }

    @Test
    public void getSuiteApiClient() {
        AdapterInstance ai = new AdapterInstance(ADAPTER_INSTANCE1);
        assertNotNull(ai.getSuiteApiClient());
        assertEquals(HOSTNAME, ai.getSuiteApiClient().getConnectionInfo().getHostname());
        assertEquals(USERNAME, ai.getSuiteApiClient().getConnectionInfo().getUsername());
        assertEquals(PASSWORD, ai.getSuiteApiClient().getConnectionInfo().getPassword());
    }

    @Test
    public void getNullSuiteApiClient() {
        AdapterInstance ai = new AdapterInstance(ADAPTER_INSTANCE2);
        assertNotNull(ai.getSuiteApiClient());
        assertEquals("", ai.getSuiteApiClient().getConnectionInfo().getHostname());
        assertEquals("", ai.getSuiteApiClient().getConnectionInfo().getUsername());
        assertEquals("", ai.getSuiteApiClient().getConnectionInfo().getPassword());
    }

    @Test
    public void getCertificates() {
        AdapterInstance ai = new AdapterInstance(ADAPTER_INSTANCE1);
        assertNotNull(ai.getCertificates());
        assertEquals(2, ai.getCertificates().size());
        assertEquals(CERT1, ai.getCertificates().get(0));
        assertEquals(CERT2, ai.getCertificates().get(1));
    }

    @Test
    public void getCollectionNumber() {
        AdapterInstance ai = new AdapterInstance(ADAPTER_INSTANCE1);
        assertEquals(COLLECTION_NUMBER, ai.getCollectionNumber());
    }

    @Test
    public void getCollectionWindow() {
        AdapterInstance ai = new AdapterInstance(ADAPTER_INSTANCE1);
        assertNotNull(ai.getCollectionWindow());
        assertEquals(START_TIME, ai.getCollectionWindow().getStartTime());
        assertEquals(END_TIME, ai.getCollectionWindow().getEndTime());
    }

    @Test
    public void getCredentialType() {
        AdapterInstance ai = new AdapterInstance(ADAPTER_INSTANCE1);
        assertEquals(CREDENTIAL_TYPE, ai.getCredentialType());
    }

    @Test
    public void getCredentialValue() {
        AdapterInstance ai = new AdapterInstance(ADAPTER_INSTANCE1);
        assertEquals(FIELD1_VALUE, ai.getCredentialValue(FIELD1));
        assertEquals(FIELD2_VALUE, ai.getCredentialValue(FIELD2));
        assertNull(ai.getCredentialValue("field3"));
    }
}