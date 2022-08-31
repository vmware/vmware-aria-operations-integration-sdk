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
        base_describe = xml.parse("res/base_describe.xml")
        yield base_describe.getroot()

        # NOTE: maybe restore back to its original state

        xml_schema.is_valid(base_describe_xml)

    def test_invalid_element(self, xml_schema, base_describe_xml):
        with pytest.raises(xmlschema.validators.exceptions.XMLSchemaValidatorError):
            base_describe_xml.append(xml.Element("NotGood"))
            xml_schema.validate(base_describe_xml)

    def test_duplicate_resource_kind_key(self, xml_schema, base_describe_xml):
        resource_kinds = base_describe_xml.find(ns("ResourceKinds"))
        resource_kinds.insert(3, xml.Element(ns("ResourceKind"), attrib={"key": "CPU", "nameKey": "0"}))

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as duplicate:
            xml_schema.validate(base_describe_xml)
        assert "duplicated value ('CPU',)" in str(duplicate.value)

    def test_duplicate_resource_attribute_key(self, xml_schema, base_describe_xml):
        resource_kind = base_describe_xml.find(ns("ResourceKinds")).find(ns("ResourceKind"))
        resource_kind.insert(0, xml.Element(ns("ResourceAttribute"), attrib={"key": "test_attribute", "nameKey": "0"}))
        resource_kind.insert(0, xml.Element(ns("ResourceAttribute"), attrib={"key": "test_attribute", "nameKey": "1"}))

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as duplicate:
            xml_schema.validate(base_describe_xml)
        assert "duplicated value ('test_attribute',)" in str(duplicate.value)

    def test_same_key_for_parent_and_child(self, xml_schema, base_describe_xml):
        resource_kinds = base_describe_xml.find(ns("ResourceKinds"))
        resource_kinds.insert(3, xml.Element(ns("ResourceKind"), attrib={"key": "CPU", "nameKey": "0"}))

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as duplicate:
            xml_schema.validate(base_describe_xml)
        assert "duplicated value ('CPU',)" in str(duplicate.value)

    def test_resource_attribute_key_inside_of_resource_group(self, xml_schema, base_describe_xml):
        resource_kinds = base_describe_xml.find(ns("ResourceKinds"))
        resource_kinds.insert(3, xml.Element(ns("ResourceKind"), attrib={"key": "CPU", "nameKey": "0"}))

        with pytest.raises(xmlschema.validators.XMLSchemaValidatorError) as duplicate:
            xml_schema.validate(base_describe_xml)
        assert "duplicated value ('CPU',)" in str(duplicate.value)
