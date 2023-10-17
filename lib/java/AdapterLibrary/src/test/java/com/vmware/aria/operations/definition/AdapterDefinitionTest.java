package com.vmware.aria.operations.definition;

import com.vmware.aria.operations.*;
import org.junit.jupiter.api.*;

import java.util.*;

class AdapterDefinitionTest {
    @Test
    public void testAdapterDefinitionJson() throws KeyException {
        AdapterDefinition ad = new AdapterDefinition(
                "adapterType",
                "Adapter Label",
                "adapterInstanceType",
                "Adapter Instance Label");
        ad.defineMetric("metric1", "Metric 1", Units.Power.GIGAWATT.getUnit());
        GroupType g = ad.defineGroup("group");
        g.defineMetric("metric2", "Metric 1");
        System.out.print(ad.getJson());
    }

    @Test
    public void testStringDefinition() throws KeyException {
        AdapterDefinition ad = new AdapterDefinition("myAdapter");
        ad.defineStringParameter("myStringParameter1");

        ad.defineStringParameter("myStringParameter2", "My Labeled String Parameter");

        ad.defineStringParameter("myStringParameter3", parameter -> {
            parameter.setLabel("Another Labeled String Parameter");
            parameter.setMaxLength(200);
            parameter.setAdvanced(true);
            parameter.setDefault("DefaultValue");
        });

        StringParameterBuilder stringParameterBuilder = new StringParameterBuilder("MyKey");
        stringParameterBuilder.setMaxLength(200);
        stringParameterBuilder.setAdvanced(true);
        stringParameterBuilder.setDefault("default");
        StringParameter myKeyParameter = stringParameterBuilder.build();
        ad.addParameter(myKeyParameter);

        System.out.print(ad.getJson());
    }

    @Test
    public void testIntegerDefinition() throws KeyException {
        AdapterDefinition ad = new AdapterDefinition("myAdapter");
        ad.defineIntegerParameter("myIntParameter1");
        ad.defineIntegerParameter("myIntParameter2", "My Labeled Int Parameter");
        ad.defineIntegerParameter("myIntParameter3", parameter -> {
            parameter.setLabel("Another Labeled Int Parameter");
            parameter.setAdvanced(true);
            parameter.setDescription("This is a description");
        });

        System.out.print(ad.getJson());
    }

    @Test
    public void testEnumDefinition() throws KeyException {
        AdapterDefinition ad = new AdapterDefinition("myAdapter");
        ad.defineEnumParameter("myEnumParameter1", List.of(
                new EnumParameter.EnumValue("yes", "Yes"),
                new EnumParameter.EnumValue("no", "No")))
        ;

        ad.defineEnumParameter("myEnumParameter2", List.of(new EnumParameter.EnumValue("yes", "Yes"), new EnumParameter.EnumValue("no", "No")), "My Labeled Enum Parameter");

        ad.defineEnumParameter("myEnumParameter3", parameter -> {
            parameter.setDescription("This is a description");
            parameter.withDefaultOption("yes", "Yes");
            parameter.withOption("no");
        });
        
        System.out.print(ad.getJson());
    }
}
