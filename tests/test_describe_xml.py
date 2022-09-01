import os.path

import xmlschema
import pytest

import xml.etree.ElementTree as xml

from vrealize_operations_integration_sdk.describe import ns


class TestSchema:

    @pytest.fixture(scope="session")  # the same XSD for all tests
    def xml_schema(self):
        return xmlschema.XMLSchema11(os.path.join("..", "doc", "describeSchema.xsd"))

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

    def test_valid_xml(self, xml_schema, base_describe_xml):
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
