import copy
import json
import random

import pytest as pytest

from validation.highlights import highlight_metric_growth, highlight_property_growth, highlight_property_value_growth, \
    highlight_relationship_growth, highlight_event_growth
from validation.result import ResultLevel
from vrealize_operations_integration_sdk.docker_wrapper import ContainerStats
from vrealize_operations_integration_sdk.serialization import CollectionBundle, LongCollectionBundle
from requests import Request


# This object is used to create mock objects with constant values
class TestObject:
    pass


class TestHighlights:
    @pytest.fixture(autouse=True)
    def constants(self):
        CONTAINER = TestObject()
        CONTAINER.current_memory_usage = [40783872, 41062400]
        CONTAINER.memory_percent_usage = [3.7982940673828125, 3.8242340087890625]
        CONTAINER.cpu_percent_usage = [0.03328320802005013, 0.03794486215538847]
        CONTAINER.previous_stats = {'cpu_stats': {
            'cpu_usage': {'total_usage': 1371830000, 'usage_in_kernelmode': 102727000,
                          'usage_in_usermode': 1269103000}, 'system_cpu_usage': 1103488650000000, 'online_cpus': 2,
            'throttling_data': {'periods': 0, 'throttled_periods': 0, 'throttled_time': 0}}}
        pytest.CONTAINER_STATISTICS = ContainerStats(CONTAINER)
        pytest.REQUEST = Request(method="POST", url='http://localhost:8080/collect',
                                 json={'adapterKey': {'name': 'good', 'adapterKind': 'HighlightsMP',
                                                      'objectKind': 'HighlightsMP_adapter_instance', 'identifiers': [
                                         {'key': 'ID', 'value': 'good', 'isPartOfUniqueness': True},
                                         {'key': 'container_memory_limit', 'value': '1024',
                                          'isPartOfUniqueness': False}]},
                                       'clusterConnectionInfo': {'userName': 'string', 'password': 'string',
                                                                 'hostName': 'string'},
                                       'certificateConfig': {'certificates': []}},
                                 headers={'Accept': 'application/json'})
        pytest.DURATION = 5
        pytest.JSON = {
            "nonExistingObjects": [],
            "relationships": [],
            "result": [
                {
                    "events": [],
                    "key": {
                        "adapterKind": "HighlightsMP",
                        "identifiers": [],
                        "name": "fist",
                        "objectKind": "Growing Object"
                    },
                    "metrics": [
                        {
                            "key": "stable number",
                            "numberValue": 42.0,
                            "timestamp": 1666796497855
                        }
                    ],
                    "properties": [
                        {
                            "key": "stable_property",
                            "stringValue": "I am stable",
                            "timestamp": 1666813121048
                        }
                    ]
                }
            ]
        }

    def test_no_highlight(self):
        """
        Test that no highlights are generated when collections don't have any object growth
        """
        response = TestObject()
        response.is_success = True
        response.text = json.dumps(pytest.JSON)
        normal_collection = LongCollectionBundle(5, 25)
        # Add ten identical collections
        for collection in range(10):
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            normal_collection.add(collection_bundle)

        highlight = normal_collection.validate()
        assert len(highlight.messages) == 0

    def test_highlight_for_growing_unique_objects(self):
        """
        Test object growth highlight is generated when the number of unique objects generated overtime is
        a clear indicator of object growth
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        growing_unique_objects_overtime = LongCollectionBundle(5, 25)
        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            growing_unique_objects_overtime.add(collection_bundle)
            _json["result"][0]["key"]["name"] = f"{collection}"

        highlight = growing_unique_objects_overtime.validate()
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed growth of 9.65") in highlight.messages

    def test_highlight_for_growing_unique_objects_two(self):
        """
        Test object growth highlight is generated when the number of unique objects generated overtime displays near the
        expected threshold
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        growing_unique_objects_overtime = LongCollectionBundle(5, 25)
        for collection in range(100):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            growing_unique_objects_overtime.add(collection_bundle)
            if collection % 3 == 0:
                _json["result"][0]["key"]["name"] = f"{collection}"

        highlight = growing_unique_objects_overtime.validate()
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed growth of 15.15") in highlight.messages

    def test_highlight_for_growing_unique_objects_with_low_object_growth(self):
        """
        Test object growth highlight is generated when the number of unique objects generated overtime is
        a indicator of object growth
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        growing_unique_objects_overtime = LongCollectionBundle(5, 25)
        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            growing_unique_objects_overtime.add(collection_bundle)
            _json["result"][0]["key"]["name"] = f"{collection}" if collection % 4 == 0 else "same_object"

        highlight = growing_unique_objects_overtime.validate()
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed growth of 6.65") in highlight.messages

    def test_no_highlight_for_growing_unique_objects_with_low_object_growth(self):
        """
        Test object growth highlight is generated not when the number of unique objects generated overtime is
        reasonable and negligible on the long run
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        growing_unique_objects_overtime = LongCollectionBundle(5, 25)
        for collection in range(100):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            growing_unique_objects_overtime.add(collection_bundle)
            _json["result"][0]["key"]["name"] = f"{collection}" if collection % 9 == 0 else "same_object"

        highlight = growing_unique_objects_overtime.validate()
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed growth of 10.80") in highlight.messages

    def test_highlight_for_high_number_of_growing_objects_per_collection(self):
        """
        Test object growth highlights is generated when the number of objects of the same type grows every collection
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        increasing_number_of_objects_per_collection = LongCollectionBundle(5, 25)
        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            increasing_number_of_objects_per_collection.add(collection_bundle)
            new_object = copy.deepcopy(pytest.JSON["result"][0])
            new_object["key"]["name"] = f"{collection}"
            _json["result"].append(new_object)

        highlight = increasing_number_of_objects_per_collection.validate()
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed growth of 9.65") in highlight.messages

    # depecated
    def test_no_highlight_for_high_number_of_growing_objects_per_collection(self):
        """
        Test object growth highlights is generated when th#e number of objects of the same type grows every collection
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        increasing_number_of_objects_per_collection = LongCollectionBundle(5, 25)
        for collection in range(100):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            increasing_number_of_objects_per_collection.add(collection_bundle)
            new_object = copy.deepcopy(pytest.JSON["result"][0])
            if collection % 9 == 0:
                new_object["key"]["name"] = f"{collection}"
                _json["result"].append(new_object)

        highlight = increasing_number_of_objects_per_collection.validate()
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed growth of 10.45") in highlight.messages

    def test_metric_highlight(self):
        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        increasing_number_of_metrics_per_collection = LongCollectionBundle(5, 25)

        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            increasing_number_of_metrics_per_collection.add(collection_bundle)
            new_metric = copy.deepcopy(pytest.JSON["result"][0]["metrics"][0])
            new_metric["key"] = f"{collection}"
            _json["result"][0]["metrics"].append(new_metric)

        highlight = highlight_metric_growth(increasing_number_of_metrics_per_collection.long_collection_statistics)
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed metric growth of 9.65") in highlight.messages

    def test_no_metric_highlight(self):
        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        changing_metric_value_per_collection = LongCollectionBundle(5, 25)

        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            changing_metric_value_per_collection.add(collection_bundle)
            _json["result"][0]["metrics"][0]["numberValue"] = random.randint(0, 100)

        highlight = highlight_metric_growth(changing_metric_value_per_collection.long_collection_statistics)
        assert len(highlight.messages) == 0

    def test_property_highlight(self):
        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        increasing_number_of_properties_per_collection = LongCollectionBundle(5, 25)

        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            increasing_number_of_properties_per_collection.add(collection_bundle)
            new_property = copy.deepcopy(pytest.JSON["result"][0]["properties"][0])
            new_property["key"] = f"{collection}"
            _json["result"][0]["properties"].append(new_property)

        highlight = highlight_property_growth(increasing_number_of_properties_per_collection.long_collection_statistics)
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed property growth of 9.65") in highlight.messages

    def test_no_property_highlight(self):
        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        stable_collection = LongCollectionBundle(5, 25)

        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            stable_collection.add(collection_bundle)

        highlight = highlight_property_growth(stable_collection.long_collection_statistics)
        assert len(highlight.messages) == 0

    def test_property_value_highlight(self):
        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        increasing_number_of_property_values_per_collection = LongCollectionBundle(5, 25)

        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            increasing_number_of_property_values_per_collection.add(collection_bundle)
            _json["result"][0]["properties"][0]["stringValue"] = f"{collection}"

        highlight = highlight_property_value_growth(
            increasing_number_of_property_values_per_collection.long_collection_statistics)
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed property value growth of 9.65") in highlight.messages

    def test_no_property_value_highlight(self):
        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        changing_metric_value_per_collection = LongCollectionBundle(5, 25)

        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            changing_metric_value_per_collection.add(collection_bundle)

        highlight = highlight_property_value_growth(changing_metric_value_per_collection.long_collection_statistics)
        assert len(highlight.messages) == 0

    def test_relationship_highlight(self):
        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        increasing_number_of_property_values_per_collection = LongCollectionBundle(5, 25)
        parent = {
            "adapterKind": "HighlightsMP",
            "identifiers": [],
            "name": "Parent",
            "objectKind": "Test Parent"
        }
        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            increasing_number_of_property_values_per_collection.add(collection_bundle)

            children = [{
                "adapterKind": "HighlightsMP",
                "identifiers": [],
                "name": f"child {collection % 2}",
                "objectKind": "Test Children"
            }]

            _json["relationships"] = [{"parent": parent, "children": children}]

        highlight = highlight_relationship_growth(
            increasing_number_of_property_values_per_collection.long_collection_statistics)
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed relationship growth of 9.65") in highlight.messages

    def test_no_relationship_highlight(self):
        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        changing_metric_value_per_collection = LongCollectionBundle(5, 25)

        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            changing_metric_value_per_collection.add(collection_bundle)

        highlight = highlight_relationship_growth(changing_metric_value_per_collection.long_collection_statistics)
        assert len(highlight.messages) == 0

    def test_event_highlight(self):
        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        increasing_number_of_property_values_per_collection = LongCollectionBundle(5, 25)

        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            increasing_number_of_property_values_per_collection.add(collection_bundle)
            events = collection * 10
            for event in range(events, events + 10):
                _json["result"][0]["events"].append(
                    dict(message=f"New event {event}", criticality="critical", fault_key="fault_key"))

        highlight = highlight_event_growth(
            increasing_number_of_property_values_per_collection.long_collection_statistics)
        assert (ResultLevel.WARNING,
                "Object of type HighlightsMP::Growing Object displayed event growth of 19.77") in highlight.messages

    def test_no_event_highlight(self):
        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        changing_metric_value_per_collection = LongCollectionBundle(5, 25)

        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            changing_metric_value_per_collection.add(collection_bundle)

        highlight = highlight_event_growth(changing_metric_value_per_collection.long_collection_statistics)
        assert len(highlight.messages) == 0
