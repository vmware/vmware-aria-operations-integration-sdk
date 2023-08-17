package com.vmware.aria.operations;

import org.junit.jupiter.params.*;
import org.junit.jupiter.params.provider.*;

import java.util.stream.*;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

class DataTest {
    public static Stream<Arguments> stringValues() {
        return Stream.of(
                Arguments.of("key"),
                Arguments.of("key_1"),
                Arguments.of("Key %"),
                Arguments.of("looooooooooooooooooooooooooooooooong keeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeey")
        );
    }

    public static Stream<Arguments> numericValues() {
        return Stream.of(
                Arguments.of(1),
                Arguments.of(59),
                Arguments.of(100L),
                Arguments.of(0.004F),
                Arguments.of(Double.MAX_VALUE)
        );
    }

    public static Stream<Arguments> timestampValues() {
        return Stream.of(
                Arguments.of(0L),
                Arguments.of(555L),
                Arguments.of(Long.MAX_VALUE)
                );
    }

    @ParameterizedTest
    @MethodSource("stringValues")
    public void metricGetKey(String key) {
        Metric metric = new Metric(key, 9.0, 1001L);
        assertEquals(key, metric.getKey());
    }

    @ParameterizedTest
    @MethodSource("numericValues")
    public void metricGetValue(Number number) {
        Metric metric = new Metric("key", number, 1001L);
        assertEquals(number.doubleValue(), metric.getDoubleValue());
    }

    @ParameterizedTest
    @MethodSource("timestampValues")
    public void metricGetTimestamp(Long timestamp) {
        Metric metric = new Metric("key", 9.0, timestamp);
        assertEquals(timestamp, metric.getTimestamp());
    }


    @ParameterizedTest
    @MethodSource("stringValues")
    public void propertyGetKey(String key) {
        Property property = new Property(key, 9.0, 1001L);
        assertEquals(key, property.getKey());
    }

    @ParameterizedTest
    @MethodSource("numericValues")
    public void propertyGetNumericValue(Number number) {
        Property property = new Property("key", number, 1001L);
        assertEquals(number.doubleValue(), property.getDoubleValue());
        assertNull(property.getStringValue());
    }

    @ParameterizedTest
    @MethodSource("stringValues")
    public void propertyGetStringValue(String string) {
        Property property = new Property("key", string, 1001L);
        assertEquals(string, property.getStringValue());
        assertNull(property.getDoubleValue());
    }

    @ParameterizedTest
    @MethodSource("timestampValues")
    public void propertyGetTimestamp(Long timestamp) {
        Property property = new Property("key", 9.0, timestamp);
        assertEquals(timestamp, property.getTimestamp());
    }
}