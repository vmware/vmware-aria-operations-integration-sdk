package com.vmware.aria.operations.definition;

import com.vmware.aria.operations.*;
import kotlinx.serialization.json.*;
import org.junit.jupiter.api.*;

class AdapterDefinitionTest {
    @Test
    public void testAdapterDefinitionJson() {
        try {
            AdapterDefinition ad = new AdapterDefinition(
                    "adapterType",
                    "Adapter Label",
                    "adapterInstanceType",
                    "Adapter Instance Label");
            ad.defineMetric("metric1", "Metric 1", Units.Power.GIGAWATT.getUnit());
            GroupType g = ad.defineGroup("group");
            g.defineMetric("metric2", "Metric 1");


            System.out.print(ad.getJson());
        } catch(KeyException e) {

        }
    }
}