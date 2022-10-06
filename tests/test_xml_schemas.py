import copy
import os
from importlib import resources

import xmlschema
import pytest

import xml.etree.ElementTree as xml

from vrealize_operations_integration_sdk.describe import ns
from vrealize_operations_integration_sdk import adapter_template
from lxml import etree


class TestDescribe:

    @pytest.fixture(scope="session")  # the same XSD for all tests
    def xml_schema(self):
        with resources.path(adapter_template, "describeSchema.xsd") as schema:
            return xmlschema.XMLSchema11(schema)

    @pytest.fixture
    def base_describe_xml(self):
        root = xml.Element(ns("AdapterKind"),
                           attrib=dict(key="TestAdapter",
                                       nameKey="1",
                                       version="1"))
        resource_kinds = xml.Element(ns("ResourceKinds"))
        base_test_resource = xml.Element(ns("ResourceKind"),
                                         attrib=dict(key="test_resource",
                                                     nameKey="3",
                                                     ))
        resource_kinds.append(base_test_resource)

        root.append(resource_kinds)
        tree = xml.ElementTree(root)
        yield tree.getroot()

    def test_valid_describe_xml(self, xml_schema, base_describe_xml):
        xml_schema.is_valid(base_describe_xml)

    def test_invalid_element(self, xml_schema, base_describe_xml):
        with pytest.raises(xmlschema.validators.exceptions.XMLSchemaValidatorError):
            base_describe_xml.append(xml.Element("NotGood"))
            xml_schema.validate(base_describe_xml)

    def test_duplicate_resource_kind_key(self, xml_schema, base_describe_xml):
        resource_kinds = base_describe_xml.find(ns("ResourceKinds"))
        duplicate = xml.Element(ns("ResourceKind"), attrib={"key": "duplicate", "nameKey": "0"})
        resource_kinds.insert(0, duplicate)
        resource_kinds.insert(0, duplicate)

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as duplicate:
            xml_schema.validate(base_describe_xml)
        assert "duplicated value ('duplicate',)" in str(duplicate.value)

    def test_duplicate_resource_attribute_key(self, xml_schema, base_describe_xml):
        resource_kind = base_describe_xml.find(ns("ResourceKinds")).find(ns("ResourceKind"))
        resource_kind.insert(0, xml.Element(ns("ResourceAttribute"), attrib={"key": "test_attribute", "nameKey": "0"}))
        resource_kind.insert(0, xml.Element(ns("ResourceAttribute"), attrib={"key": "test_attribute", "nameKey": "1"}))

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as duplicate:
            xml_schema.validate(base_describe_xml)
        assert "duplicated value ('test_attribute',)" in str(duplicate.value)

    def test_resource_attribute_key_inside_of_resource_group(self, xml_schema, base_describe_xml):
        resource_kind = base_describe_xml.find(ns("ResourceKinds")).find(ns("ResourceKind"))
        resource_group = xml.Element(ns("ResourceGroup"), attrib=dict(key="test_group", nameKey="4"))
        resource_kind.append(resource_group)

        attribute = xml.Element(ns("ResourceAttribute"), attrib={"key": "twin", "nameKey": "0"})

        resource_kind.insert(0, attribute)
        resource_group.insert(0, attribute)

        assert xml_schema.is_valid(base_describe_xml)

    def test_string_property(self, xml_schema, base_describe_xml):
        resource_kind = base_describe_xml.find(ns("ResourceKinds")).find(ns("ResourceKind"))
        _property = xml.Element(ns("ResourceAttribute"),
                                attrib={"key": "attribute", "nameKey": "0", "dataType": "string", "isProperty": "true"})
        resource_kind.insert(0, _property)

        assert xml_schema.is_valid(base_describe_xml)

    def test_string_metric_not_allowed(self, xml_schema, base_describe_xml):
        resource_kind = base_describe_xml.find(ns("ResourceKinds")).find(ns("ResourceKind"))
        _property = xml.Element(ns("ResourceAttribute"),
                                attrib={"key": "attribute", "nameKey": "0", "dataType": "string"})
        resource_kind.insert(0, _property)

        assert not xml_schema.is_valid(base_describe_xml)


class TestAlertsRecommendationsAndSymptoms:
    @pytest.fixture(scope="session")
    def content_xml_schema(self):
        with resources.path(adapter_template, "alertDefinitionSchema.xsd") as schema:
            return xmlschema.XMLSchema11(schema)

    @pytest.fixture
    def modified_content(self):
        yield etree.parse("res/modified_alert.xml")

    @pytest.fixture
    def generated_content(self):
        yield etree.parse("res/generated_alert.xml")

    def test_valid_content_xml_generated_alert(self, content_xml_schema, generated_content):
        content_xml_schema.validate(generated_content)

    def test_valid_content_xml_modified_alert(self, content_xml_schema, modified_content):
        content_xml_schema.validate(modified_content)

    def test_invalid_element_on_content_xml(self, content_xml_schema, generated_content, modified_content):
        invalid_element = etree.Element("NotGood")
        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError):
            generated_content.getroot().append(invalid_element)
            content_xml_schema.validate(generated_content)

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError):
            modified_content.getroot().append(invalid_element)
            content_xml_schema.validate(modified_content)

    def test_alert_definition_duplicate(self, content_xml_schema, generated_content):
        alert_definitions = generated_content.getroot().find("AlertDefinitions")
        alert_definition = alert_definitions.find("AlertDefinition")
        alert_definitions.insert(0, copy.deepcopy(alert_definition))

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as duplicate:
            content_xml_schema.validate(generated_content)

        assert "duplicated" in str(duplicate.value)

    def test_alert_definition_missing_properties(self, content_xml_schema, generated_content):
        alert_definition = generated_content.find("AlertDefinitions").find("AlertDefinition")
        alert_definition.clear()

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as missing:
            content_xml_schema.validate(generated_content)
        assert "missing required attribute" in str(missing.value)

    def test_missing_state_element_from_alert_definition(self, content_xml_schema, generated_content):
        alert_definition = etree.Element("AlertDefinition",
                                         attrib=dict(adapterKind="TestAdapterKind", description="120",
                                                     id="AlertDefinition-New", name="New Alert",
                                                     resourceKind="TestResourceKind", subType="18", type="15"))

        alert_definitions = generated_content.find("AlertDefinitions")
        alert_definitions.insert(0, alert_definition)

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as missing:
            content_xml_schema.validate(generated_content)

        assert "The content of element 'AlertDefinition' is not complete. Tag 'State' expected" in str(missing)

    def test_symptom_definition_id_duplicate(self, content_xml_schema, generated_content):
        symptom_definitions = generated_content.find("SymptomDefinitions")
        symptom_definition = symptom_definitions.find("SymptomDefinition")
        symptom_definitions.insert(0, copy.deepcopy(symptom_definition))

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as duplicate:
            content_xml_schema.validate(generated_content)

        assert "attribute id" in str(duplicate)

    def test_symptom_definition_missing_properties(self, content_xml_schema, generated_content):
        symptom_definition: xml.Element = generated_content.find("SymptomDefinitions").find("SymptomDefinition")
        symptom_definition.clear()

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as missing:
            content_xml_schema.validate(generated_content)
        assert "missing required attribute" in str(missing.value)


class TestTraversals:
    @pytest.fixture(scope="session")  # the same XSD for all tests
    def traversal_schema(self):
        with resources.path(adapter_template, "traversalSpecsSchema.xsd") as schema:
            return xmlschema.XMLSchema11(schema)

    @pytest.fixture
    def base_traversal_xml(self):
        yield etree.parse("res/traversal.xml")

    def test_valid_traversal_xml(self, traversal_schema, base_traversal_xml):
        traversal_schema.is_valid(base_traversal_xml)

    def test_invalid_element(self, traversal_schema, base_traversal_xml):
        root = base_traversal_xml.getroot()
        root.insert(0, etree.Element("Invalid"))

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as invalid:
            traversal_schema.validate(base_traversal_xml)

        assert "Unexpected child with tag 'Invalid' at position 1" in str(invalid.value)

    def test_add_valid_traversal(self, traversal_schema, base_traversal_xml):
        traversal_spec_kinds = base_traversal_xml.find("TraversalSpecKinds")
        new_traversal = etree.Element("TraversalSpecKind",
                                      attrib=dict(name="New Traversal"),
                                      rootAdapterKind="ContentTestMP",
                                      rootResourceKind="System",
                                      usedFor="ENV",
                                      description="New Traversal description")
        new_traversal.insert(0, etree.Element("ResourcePath", attrib=dict(path="ContentTestMP::System||ContentTestMP::CPU::child")))
        traversal_spec_kinds.insert(0, new_traversal)

        traversal_schema.validate(base_traversal_xml)
