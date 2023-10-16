package com.vmware.aria.operations;

import org.junit.jupiter.api.*;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

public final class ObjectTest {
    Key simpleKey = new Key("adapter", "object", "name");
    Key simpleKey2 = new Key("adapter", "object", "name2");
    Key identifierKey = new Key("adapter", "object", "name", Arrays.asList(
            new Identifier("id1", "value1"),
            new Identifier("id2", "value2"),
            new Identifier("id3", "value3", false)
    ));

    @Test
    public final void getHasUpdatedChildren$AdapterLibrary() {
        Object object = new Object(simpleKey);
        Object child = new Object(simpleKey2);
        Object parent = new Object(identifierKey);
        assertFalse(object.getHasUpdatedChildren$IntegrationSDKAdapterLibrary());
        object.addParent(parent);
        assertFalse(object.getHasUpdatedChildren$IntegrationSDKAdapterLibrary());
        object.addChild(child);
        assertTrue(object.getHasUpdatedChildren$IntegrationSDKAdapterLibrary());
    }

    @Test
    public final void getAdapterType() {
        Object object = new Object(simpleKey);
        assertEquals("adapter", object.getAdapterType());
    }

    @Test
    public final void getObjectType() {
        Object object = new Object(simpleKey);
        assertEquals("object", object.getObjectType());
    }

    @Test
    public final void getName() {
        Object object = new Object(simpleKey);
        assertEquals("name", object.getName());
    }

    @Test
    public final void getIdentifierValue() {
        Object object = new Object(identifierKey);
        assertEquals("value2", object.getIdentifierValue("id2"));
    }

    @Test
    public final void getIdentifierDefaultValue() {
        Object object = new Object(identifierKey);
        assertEquals("default", object.getIdentifierValue("id4", "default"));
    }

    @Test
    public final void addMetric() {
        Object object = new Object(simpleKey);
        Metric metric = new Metric("key", 1.0);
        object.addMetric(metric);
        assertTrue(object.getMetric("key").contains(metric));
    }

    @Test
    public final void addMetrics() {
        Object object = new Object(simpleKey);
        Metric metric1 = new Metric("key1", 1.0);
        Metric metric2 = new Metric("key2", 1.0);
        object.addMetrics(Arrays.asList(metric1, metric2));
        assertTrue(object.getMetric("key1").contains(metric1));
        assertTrue(object.getMetric("key2").contains(metric2));
    }

    @Test
    public final void withMetric() {
        Object object = new Object(simpleKey);
        object.withMetric("key", 1.0);
        assertEquals(1, object.getMetric("key").size());
        assertEquals("key", object.getMetric("key").stream().findFirst().get().getKey());
        assertEquals(1.0, object.getMetric("key").stream().findFirst().get().getDoubleValue());
    }

    @Test
    public final void withMetric2() {
        Object object = new Object(simpleKey);
        Long timestamp = System.currentTimeMillis();
        object.withMetric("key", 1.0, timestamp);
        assertEquals(1, object.getMetric("key").size());
        assertEquals("key", object.getMetric("key").stream().findFirst().get().getKey());
        assertEquals(1.0, object.getMetric("key").stream().findFirst().get().getDoubleValue());
        assertEquals(timestamp, object.getMetric("key").stream().findFirst().get().getTimestamp());
    }

    @Test
    public final void getMetric() {
        Object object = new Object(simpleKey);
        Metric metric1 = new Metric("key", 1.0);
        Metric metric2 = new Metric("key", 2.0);
        List<Metric> metrics = Arrays.asList(metric1, metric2);
        object.addMetrics(metrics);
        assertTrue(object.getMetric("key").containsAll(metrics));
    }

    @Test
    public final void getMetricValues() {
        Object object = new Object(simpleKey);
        Metric metric1 = new Metric("key", 1.0);
        Metric metric2 = new Metric("key", 2.0);
        List<Metric> metrics = Arrays.asList(metric1, metric2);
        object.addMetrics(metrics);
        assertEquals(Arrays.asList(1.0, 2.0), object.getMetricValues("key"));
    }

    @Test
    public final void getLastMetricValue() {
        Object object = new Object(simpleKey);
        Metric metric1 = new Metric("key", 1.0);
        Metric metric2 = new Metric("key", 2.0);
        List<Metric> metrics = Arrays.asList(metric1, metric2);
        object.addMetrics(metrics);
        assertEquals(2.0, object.getLastMetricValue("key"));
    }

    @Test
    public final void addProperty() {
        Object object = new Object(simpleKey);
        Property property = new NumericProperty("key", 1.0);
        object.addProperty(property);
        assertTrue(object.getProperty("key").contains(property));
    }

    @Test
    public final void addProperties() {
        Object object = new Object(simpleKey);
        Property property1 = new NumericProperty("key1", 1.0);
        Property property2 = new NumericProperty("key2", 1.0);
        object.addProperties(Arrays.asList(property1, property2));
        assertTrue(object.getProperty("key1").contains(property1));
        assertTrue(object.getProperty("key2").contains(property2));
    }

    @Test
    public final void withNumericProperty() {
        Object object = new Object(simpleKey);
        object.withProperty("key", 1.0);
        assertEquals(1, object.getProperty("key").size());
        assertEquals("key", object.getProperty("key").stream().findFirst().get().getKey());
        assertEquals(1.0, ((NumericProperty) object.getProperty("key").stream().findFirst().get()).getDoubleValue());
    }

    @Test
    public final void withNumericProperty2() {
        Object object = new Object(simpleKey);
        Long timestamp = System.currentTimeMillis();
        object.withProperty("key", 1.0, timestamp);
        assertEquals(1, object.getProperty("key").size());
        assertEquals("key", object.getProperty("key").stream().findFirst().get().getKey());
        assertEquals(1.0, ((NumericProperty) object.getProperty("key").stream().findFirst().get()).getDoubleValue());
        assertEquals(timestamp, object.getProperty("key").stream().findFirst().get().getTimestamp());
    }

    @Test
    public final void withStringProperty() {
        Object object = new Object(simpleKey);
        object.withProperty("key", "string");
        assertEquals(1, object.getProperty("key").size());
        assertEquals("key", object.getProperty("key").stream().findFirst().get().getKey());
        assertEquals("string", ((StringProperty) object.getProperty("key").stream().findFirst().get()).getStringValue());
    }

    @Test
    public final void withStringProperty2() {
        Object object = new Object(simpleKey);
        Long timestamp = System.currentTimeMillis();
        object.withProperty("key", "string", timestamp);
        assertEquals(1, object.getProperty("key").size());
        assertEquals("key", object.getProperty("key").stream().findFirst().get().getKey());
        assertEquals("string", ((StringProperty) object.getProperty("key").stream().findFirst().get()).getStringValue());
        assertEquals(timestamp, object.getProperty("key").stream().findFirst().get().getTimestamp());
    }

    @Test
    public final void getProperty() {
        Object object = new Object(simpleKey);
        Property property1 = new NumericProperty("key", 1.0);
        Property property2 = new NumericProperty("key", 2.0);
        List<Property> properties = Arrays.asList(property1, property2);
        object.addProperties(properties);
        assertTrue(object.getProperty("key").containsAll(properties));
    }

    @Test
    public final void getNumericPropertyValues() {
        Object object = new Object(simpleKey);
        Property property1 = new NumericProperty("key", 1.0);
        Property property2 = new NumericProperty("key", 2.0);
        List<Property> properties = Arrays.asList(property1, property2);
        object.addProperties(properties);
        assertEquals(Arrays.asList(1.0, 2.0), object.getNumericPropertyValues("key"));
        assertEquals(Collections.emptyList(), object.getStringPropertyValues("key"));
    }

    @Test
    public final void getStringPropertyValues() {
        Object object = new Object(simpleKey);
        Property property1 = new StringProperty("key", "value1");
        Property property2 = new StringProperty("key", "value2");
        List<Property> properties = Arrays.asList(property1, property2);
        object.addProperties(properties);
        assertEquals(Arrays.asList("value1", "value2"), object.getStringPropertyValues("key"));
        assertEquals(Collections.emptyList(), object.getNumericPropertyValues("key"));
    }

    @Test
    public final void getLastNumericPropertyValue() {
        Object object = new Object(simpleKey);
        Property property1 = new NumericProperty("key", 1.0);
        Property property2 = new NumericProperty("key", 2.0);
        List<Property> properties = Arrays.asList(property1, property2);
        object.addProperties(properties);
        assertEquals(2.0, object.getLastNumericPropertyValue("key"));
        assertEquals(Collections.emptyList(), object.getStringPropertyValues("key"));
    }

    @Test
    public final void getLastStringPropertyValue() {
        Object object = new Object(simpleKey);
        Property property1 = new StringProperty("key", "value1");
        Property property2 = new StringProperty("key", "value2");
        List<Property> properties = Arrays.asList(property1, property2);
        object.addProperties(properties);
        assertEquals("value2", object.getLastStringPropertyValue("key"));
        assertEquals(Collections.emptyList(), object.getNumericPropertyValues("key"));
    }

    @Test
    public final void addEvent() {
        Object object = new Object(simpleKey);
        Event event = new Event("message");
        assertEquals(0, object.getEvents().size());
        object.addEvent(event);
        assertEquals(1, object.getEvents().size());
        assertEquals("message", object.getEvents().get(0).getMessage());
    }

    @Test
    public final void addEvents() {
        Object object = new Object(simpleKey);
        Event event1 = new Event("message");
        Event event2 = new Event("message2");
        object.addEvents(Arrays.asList(event1, event2));
        assertEquals(2, object.getEvents().size());
    }

    @Test
    public final void withEvent() {
        Object object = new Object(simpleKey);
        object.withEvent("message", Criticality.CRITICAL);
        assertEquals(1, object.getEvents().size());
        assertEquals(Criticality.CRITICAL.getId(), object.getEvents().get(0).getCriticality());
    }

    @Test
    public final void withEvent1() {
        Object object = new Object(simpleKey);
        object.withEvent("message", Criticality.CRITICAL, "key");
        assertEquals(1, object.getEvents().size());
        assertEquals("key", object.getEvents().get(0).getFaultKey());
    }

    @Test
    public final void withEvent2() {
        Object object = new Object(simpleKey);
        object.withEvent("message", Criticality.CRITICAL, "key", false);
        assertEquals(1, object.getEvents().size());
        assertEquals(false, object.getEvents().get(0).getAutoCancel());
    }

    @Test
    public final void withEvent3() {
        Object object = new Object(simpleKey);
        object.withEvent("message", Criticality.CRITICAL, "key", false, 100L);
        assertEquals(1, object.getEvents().size());
        assertEquals(100L, object.getEvents().get(0).getStartDate());
    }

    @Test
    public final void withEvent4() {
        Object object = new Object(simpleKey);
        object.withEvent("message", Criticality.CRITICAL, "key", false, 100L, 150L);
        assertEquals(150L, object.getEvents().get(0).getUpdateDate());
    }

    @Test
    public final void withEvent5() {
        Object object = new Object(simpleKey);
        object.withEvent("message", Criticality.CRITICAL, "key", false, 100L, 150L, 200L);
        assertEquals(1, object.getEvents().size());
        assertEquals(200L, object.getEvents().get(0).getCancelDate());
    }

    @Test
    public final void withEvent6() {
        Object object = new Object(simpleKey);
        object.withEvent("message", Criticality.CRITICAL, "key", false, 100L, 150L, 200L, 5);
        assertEquals(1, object.getEvents().size());
        assertEquals(5, object.getEvents().get(0).getWatchWaitCycle());
    }

    @Test
    public final void withEvent7() {
        Object object = new Object(simpleKey);
        object.withEvent("message", Criticality.CRITICAL, "key", false, 100L, 150L, 200L, 5, 5);
        assertEquals(1, object.getEvents().size());
        assertEquals(5, object.getEvents().get(0).getCancelWaitCycle());
    }

    @Test
    public final void addParent() {
        Object object = new Object(simpleKey);
        Object parent = new Object(simpleKey2);
        object.addParent(parent);
        assertTrue(object.getParents().contains(parent.getKey()));
        assertTrue(parent.getChildren().contains(object.getKey()));
    }

    @Test
    public final void addParents() {
        Object object = new Object(simpleKey);
        Object parent = new Object(simpleKey2);
        Object parent2 = new Object(identifierKey);
        object.addParents(Arrays.asList(parent, parent2));
        assertTrue(object.getParents().containsAll(Arrays.asList(parent.getKey(), parent2.getKey())));
        assertTrue(parent.getChildren().contains(object.getKey()));
        assertTrue(parent2.getChildren().contains(object.getKey()));
    }

    @Test
    public final void addChild() {
        Object object = new Object(simpleKey);
        Object child = new Object(simpleKey2);
        object.addChild(child);
        assertTrue(object.getChildren().contains(child.getKey()));
        assertTrue(child.getParents().contains(object.getKey()));
    }

    @Test
    public final void addChildren() {
        Object object = new Object(simpleKey);
        Object child = new Object(simpleKey2);
        Object child2 = new Object(identifierKey);
        object.addChildren(Arrays.asList(child, child2));
        assertTrue(object.getChildren().containsAll(Arrays.asList(child.getKey(), child2.getKey())));
        assertTrue(child.getParents().contains(object.getKey()));
        assertTrue(child2.getParents().contains(object.getKey()));
    }

    @Test
    public final void hasContent() {
        Object object = new Object(simpleKey);
        assertFalse(object.hasContent());
    }

    @Test
    public final void hasContent2() {
        Object object = new Object(simpleKey);
        object.withMetric("key", 1);
        assertTrue(object.hasContent());
    }

    @Test
    public final void hasContent3() {
        Object object = new Object(simpleKey);
        object.withProperty("key", 1);
        assertTrue(object.hasContent());
    }

    @Test
    public final void hasContent4() {
        Object object = new Object(simpleKey);
        object.withEvent("message");
        assertTrue(object.hasContent());
    }

    @Test
    public final void getKey() {
        Object object = new Object(simpleKey);
        assertEquals(simpleKey, object.getKey());
    }
}
