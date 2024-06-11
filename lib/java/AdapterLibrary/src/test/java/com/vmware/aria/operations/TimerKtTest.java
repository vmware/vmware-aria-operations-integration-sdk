package com.vmware.aria.operations;

import org.junit.jupiter.api.*;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TimerKtTest {
    // all durations in milliseconds
    Long sleep1Duration = 10L;
    Long noOpDuration = 0L;
    Long sleep2Duration = 40L;
    Long tolerance = 10L;

    @BeforeEach
    public void reset() {
        Timing.clearTimers();
    }

    @Test
    public void time() {
        // This adds a timer to the graph, but we can't access the timer directly
        Integer i = Timing.time("Inner Timer 1", () -> {
            sleep(sleep1Duration);
            return 5;
        });
        assertEquals(5, i);
    }

    @Test
    public void timeException() {
        // This adds a timer to the graph, but we can't access the timer directly
        try {
            Integer i = Timing.time("Timer 1", () -> {
                sleep(sleep1Duration);
                throw new Exception("exception");
            });
        } catch (Exception e) {
            // do nothing
        }
        Timer.Companion.getTimers$integration_sdk_adapter_library().forEach((item) -> {
            assertNotNull(item.getEndTime$integration_sdk_adapter_library());
        });

    }

    @Test
    public void getDuration() {
        Timer timer = new Timer("Timer");
        sleep(sleep1Duration);
        timer.stop();
        assertWithinTolerance(sleep1Duration, tolerance, timer.getDuration());
    }

    @Test
    public void getDurationWithoutStopping() {
        Timer timer = new Timer("Timer");
        assertEquals(Long.MAX_VALUE, timer.getDuration());
    }

    @Test
    public void getName() {
        Timer timer = new Timer("Timer");
        assertEquals("Timer", timer.getName());
    }

    @Test
    public void graph1() {
        // Note: The Timing.time method is nicer in Kotlin
        Integer value = Timing.time("Long Timer", () -> {
            Timing.time("Inner Timer 1", () -> {
                sleep(sleep1Duration);
                return null;
            });
            Timing.time("No-op timer", () -> null);
            return Timing.time("Inner Timer 2", () -> {
                sleep(sleep2Duration);
                return 5;
            });
        });
        assertEquals(5, value);

        // Unfortunately no easy way to programmatically test this without adding
        // significant changes to the API that would only be useful for this test.
        System.out.println(Timing.graph());
    }

    @Test
    public void graph2() {
        Timer timer = new Timer("Long Timer");
        Timer innerTimer1 = new Timer("Inner Timer 1");
        sleep(sleep1Duration);
        innerTimer1.stop();
        Timer noOpTimer = new Timer("No-op timer");
        noOpTimer.stop();
        Timer innerTimer2 = new Timer("Inner Timer 2");
        sleep(sleep2Duration);
        innerTimer2.stop();
        timer.stop();

        assertWithinTolerance(sleep1Duration, tolerance, innerTimer1.getDuration());
        assertWithinTolerance(noOpDuration, tolerance, noOpTimer.getDuration());
        assertWithinTolerance(sleep2Duration, tolerance, innerTimer2.getDuration());
        assertWithinTolerance(sleep1Duration + sleep2Duration, tolerance * 2, timer.getDuration());

        // Unfortunately no easy way to programmatically test this without adding
        // significant changes to the API that would only be useful for this test.
        System.out.println(Timing.graph());
    }

    @Test
    public void graph3() {
        // print a graph
        assertTrue(Timing.graph().isEmpty());
    }

    private void sleep(Long milliseconds) {
        try {
            Thread.sleep(milliseconds);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }

    private void assertWithinTolerance(Long expected, Long tolerance, Long actual) {
        assertTrue(actual >= expected - tolerance);
        assertTrue(actual <= expected + tolerance);
    }
}