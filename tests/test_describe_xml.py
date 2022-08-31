import os.path

import xmlschema
import pytest

import xml.etree.ElementTree as xml

from vrealize_operations_integration_sdk.describe import ns


class Element:
    def __init__(self, element, key, name_key, **attributes):
        self.attributes = {
            "key": key,
            "nameKey": name_key,
            **attributes
        }
        self.element = xml.Element(tag=element, attrib=self.attributes)


class ResourceIdentifier(Element):
    def __init__(self, key, name_key, type):
        super().__init__("ResourceIdentifier", key, name_key)


class ResourceAttribute(Element):
    def __init__(self, key, name_key):
        super().__init__("ResourceAttribute", key, name_key)


class TestSchema:

    @pytest.fixture(scope="session")  # the same XSD for all tests
    def xml_schema(self):
        return xmlschema.XMLSchema11(os.path.join("..", "doc", "describeSchema.xsd"))

    @pytest.fixture
    def base_describe_xml(self):
        base_describe = xml.parse("res/base_describe.xml")
        yield base_describe.getroot()

        base_describe = base_describe

    def test_valid_xml(self, xml_schema, base_describe_xml):
        xml_schema.is_valid(base_describe_xml)

    def test_malformed_xml(self):
        # with pytest.raises(RuntimeError) as excinfo:
        pass

    def test_duplicate_resource_kind_key(self):
        pass

    def test_duplicate_resource_attribute_key(self):
        pass

    def test_same_key_for_parent_and_child(self):
        pass

    def test_resource_attribute_key_inside_of_resource_group(self):
        pass
