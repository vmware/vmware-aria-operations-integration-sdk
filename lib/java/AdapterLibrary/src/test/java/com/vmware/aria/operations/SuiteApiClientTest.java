package com.vmware.aria.operations;

import com.github.tomakehurst.wiremock.client.*;
import com.github.tomakehurst.wiremock.common.*;
import com.github.tomakehurst.wiremock.junit5.*;
import kotlinx.serialization.json.*;
import kotlinx.serialization.json.Json;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.*;

import java.util.*;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static org.junit.jupiter.api.Assertions.*;

@WireMockTest
class SuiteApiClientTest {
    @RegisterExtension
    static WireMockExtension wm1 = WireMockExtension.newInstance()
            .options(wireMockConfig().notifier(new ConsoleNotifier(true)))
            .options(wireMockConfig().dynamicPort().dynamicHttpsPort())
            .build();

    @BeforeEach
    public void setupTokenStubs() {
        wm1.stubFor(WireMock.post("/suite-api/api/auth/token/acquire").willReturn(aResponse().withStatus(401)));
        wm1.stubFor(WireMock.post("/suite-api/api/auth/token/acquire").withRequestBody(equalToJson("""
                {
                    "username": "username",
                    "authSource": "LOCAL",
                    "password": "password"
                }
                """)).willReturn(okJson("""
                {
                    "token": "b338d29b-3f55-430a-b2c3-fbfc4c779622::b0e3f82c-d7c2-491c-a44c-f500ac291245",
                    "validity": 2553906490535,
                    "expiresAt": "Saturday, March 30, 2019 12:41:30 AM UTC",
                    "roles": []
                }
                """)));
        wm1.stubFor(WireMock.post("/suite-api/api/auth/token/release").willReturn(ok()));
    }

    public void verifyToken() {
        wm1.verify(1, postRequestedFor(urlEqualTo("/suite-api/api/auth/token/acquire")));
    }


    @Test
    public void getMaxConnections() {
        try (SuiteApiClient client = new SuiteApiClient(new SuiteApiConnectionInfo("localhost", "username", "password"), 15)) {
            assertEquals(15, client.getMaxConnections());
        }
    }

    @Test
    public void setMaxConnections() {
        try (SuiteApiClient client = new SuiteApiClient(new SuiteApiConnectionInfo("localhost", "username", "password"), 15)) {
            client.setMaxConnections(20);
            assertEquals(20, client.getMaxConnections());
        }
    }

    @Test
    public void getConnectionInfo() {
        try (SuiteApiClient client = new SuiteApiClient(new SuiteApiConnectionInfo("localhost", "username", "password"))) {
            assertEquals("localhost", client.getConnectionInfo().getHostname());
            assertEquals("username", client.getConnectionInfo().getUsername());
            assertEquals("password", client.getConnectionInfo().getPassword());
            assertEquals(443, client.getConnectionInfo().getPort());
        }
    }


    @Test
    public void get() {
        wm1.stubFor(WireMock.get("/suite-api/test/").willReturn(okJson("""
                {
                    "test": "result"
                }
                """)));

        try (SuiteApiClient client = new SuiteApiClient(new SuiteApiConnectionInfo("localhost", "username", "password", wm1.getHttpsPort(), false))) {
            JsonObject response = client.get("test/");
            assertEquals("result", ((JsonPrimitive) Objects.requireNonNull(response.get("test"))).getContent());
        } catch (SuiteApiClientException e) {
            fail();
        }
        verifyToken();
    }

    @Test
    public void get401() {
        assertThrows(SuiteApiClientException.class, () -> {
            try {
                try (SuiteApiClient client = new SuiteApiClient(new SuiteApiConnectionInfo("localhost", "username", "BAD_password", wm1.getHttpsPort(), false))) {
                    JsonObject response = client.get("test/");
                }
            } catch (SuiteApiClientException e) {
                assertEquals(401, e.getResponseCode());
                throw e;
            }
        });
        verifyToken();
    }

    @Test
    public void get404() {
        assertThrows(SuiteApiClientException.class, () -> {
            try {
                try (SuiteApiClient client = new SuiteApiClient(new SuiteApiConnectionInfo("localhost", "username", "password", wm1.getHttpsPort(), false))) {
                    JsonObject response = client.get("test/");
                }
            } catch (SuiteApiClientException e) {
                assertEquals(404, e.getResponseCode());
                throw e;
            }
        });
        verifyToken();
    }

    @Test
    public void getPaged() {
        wm1.stubFor(WireMock.get("/suite-api/test/?page=0&pageSize=2").willReturn(okJson("""
                {
                    "test": ["one", "two"],
                    "pageInfo": {
                        "totalCount": 3
                    }
                }
                """)));
        wm1.stubFor(WireMock.get("/suite-api/test/?page=1&pageSize=2").willReturn(okJson("""
                {
                    "test": ["three"],
                    "pageInfo": {
                        "totalCount": 3
                    }
                }
                """)));

        try (SuiteApiClient client = new SuiteApiClient(new SuiteApiConnectionInfo("localhost", "username", "password", wm1.getHttpsPort(), false))) {
            JsonObject response = client.getPaged("test/", "test", 2);
            assertEquals(3, ((JsonArray) Objects.requireNonNull(response.get("test"))).size());
            assertTrue(((JsonArray) Objects.requireNonNull(response.get("test"))).containsAll(List.of(
                    JsonElementKt.JsonPrimitive("one"),
                    JsonElementKt.JsonPrimitive("two"),
                    JsonElementKt.JsonPrimitive("three")
            )));
        } catch (SuiteApiClientException e) {
            fail();
        }
        verifyToken();
    }

    @Test
    public void post() {
        wm1.stubFor(WireMock.post("/suite-api/test/").withRequestBody(equalToJson("{}")).willReturn(okJson("""
                {
                    "test": "result"
                }
                """)));

        try (SuiteApiClient client = new SuiteApiClient(new SuiteApiConnectionInfo("localhost", "username", "password", wm1.getHttpsPort(), false))) {
            JsonObject response = client.post("test/", (JsonObject) Json.Default.parseToJsonElement("{}"));
            assertEquals("result", ((JsonPrimitive) Objects.requireNonNull(response.get("test"))).getContent());
        } catch (SuiteApiClientException e) {
            fail();
        }
        verifyToken();
    }

    @Test
    public void postPaged() {
        wm1.stubFor(WireMock.post("/suite-api/test/?page=0&pageSize=2").withRequestBody(equalToJson("{}")).willReturn(okJson("""
                {
                    "test": ["one", "two"],
                    "pageInfo": {
                        "totalCount": 3
                    }
                }
                """)));
        wm1.stubFor(WireMock.post("/suite-api/test/?page=1&pageSize=2").withRequestBody(equalToJson("{}")).willReturn(okJson("""
                {
                    "test": ["three"],
                    "pageInfo": {
                        "totalCount": 3
                    }
                }
                """)));
        try (SuiteApiClient client = new SuiteApiClient(new SuiteApiConnectionInfo("localhost", "username", "password", wm1.getHttpsPort(), false))) {
            JsonObject response = client.postPaged("test/", (JsonObject) Json.Default.parseToJsonElement("{}"), "test", 2);
            assertTrue(((JsonArray) Objects.requireNonNull(response.get("test"))).containsAll(List.of(
                    JsonElementKt.JsonPrimitive("one"),
                    JsonElementKt.JsonPrimitive("two"),
                    JsonElementKt.JsonPrimitive("three")
            )));
        } catch (SuiteApiClientException e) {
            fail();
        }
        verifyToken();
    }

    @Test
    public void delete() {
        wm1.stubFor(WireMock.delete("/suite-api/test/").willReturn(ok()));

        try (SuiteApiClient client = new SuiteApiClient(new SuiteApiConnectionInfo("localhost", "username", "password", wm1.getHttpsPort(), false))) {
            client.delete("test/");
        } catch (SuiteApiClientException e) {
            fail();
        }
        verifyToken();
    }
}