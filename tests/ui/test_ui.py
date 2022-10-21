import copy
import json

import pytest as pytest

from vrealize_operations_integration_sdk.docker_wrapper import ContainerStats
from vrealize_operations_integration_sdk.mp_test import ui_highlight
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
                    "metrics": [],
                    "properties": []
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
        normal_collection = LongCollectionBundle(5)
        # Add ten identical collections
        for collection in range(10):
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            normal_collection.add(collection_bundle)

        highlight = ui_highlight(normal_collection.long_collection_statistics, "file_name.txt", "verbosity")
        assert "No object growth detected" in highlight

    def test_highlight_for_growing_unique_objects(self):
        """
        Test object growth highlight is generated when the number of unique objects generated overtime is
        a clear indicator of object growth
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        growing_unique_objects_overtime = LongCollectionBundle(5)
        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            growing_unique_objects_overtime.add(collection_bundle)
            _json["result"][0]["key"]["name"] = f"{collection}"

        highlight = ui_highlight(growing_unique_objects_overtime.long_collection_statistics, "file_name.txt", "verbosity")
        assert "Object of type HighlightsMP::Growing Object displayed growth of 25.89" in highlight

    def test_highlight_for_growing_unique_objects_two(self):
        """
        Test object growth highlight is generated when the number of unique objects generated overtime displays near the
        expected threshold
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        growing_unique_objects_overtime = LongCollectionBundle(5)
        for collection in range(100):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            growing_unique_objects_overtime.add(collection_bundle)
            if collection % 3 == 0:
                _json["result"][0]["key"]["name"] = f"{collection}"

        highlight = ui_highlight(growing_unique_objects_overtime.long_collection_statistics, "file_name.txt", "verbosity")
        assert "Object of type HighlightsMP::Growing Object displayed growth of 3.59" in highlight

    def test_highlight_for_growing_unique_objects_with_low_object_growth(self):
        """
        Test object growth highlight is generated when the number of unique objects generated overtime is
        a indicator of object growth
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        growing_unique_objects_overtime = LongCollectionBundle(5)
        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            growing_unique_objects_overtime.add(collection_bundle)
            _json["result"][0]["key"]["name"] = f"{collection}" if collection % 4 == 0 else "same_object"

        highlight = ui_highlight(growing_unique_objects_overtime.long_collection_statistics, "file_name.txt", "verbosity")
        assert "Object displayed growth of 17.46" in highlight

    def test_no_highlight_for_growing_unique_objects_with_low_object_growth(self):
        """
        Test object growth highlight is generated not when the number of unique objects generated overtime is
        reasonable and negligible on the long run
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        growing_unique_objects_overtime = LongCollectionBundle(5)
        for collection in range(100):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            growing_unique_objects_overtime.add(collection_bundle)
            _json["result"][0]["key"]["name"] = f"{collection}" if collection % 9 == 0 else "same_object"

        highlight = ui_highlight(growing_unique_objects_overtime.long_collection_statistics, "file_name.txt", "verbosity")
        assert "Object of type HighlightsMP::Growing Object displayed negligible growth (2.60)" in highlight

    def test_highlight_for_high_number_of_growing_objects_per_collection(self):
        """
        Test object growth highlights is generated when the number of objects of the same type grows every collection
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        increasing_number_of_objects_per_collection = LongCollectionBundle(5)
        for collection in range(10):
            response.text = json.dumps(_json)
            collection_bundle = CollectionBundle(pytest.REQUEST, copy.deepcopy(response), pytest.DURATION,
                                                 pytest.CONTAINER_STATISTICS)
            collection_bundle.collection_number = collection
            increasing_number_of_objects_per_collection.add(collection_bundle)
            new_object = copy.deepcopy(pytest.JSON["result"][0])
            new_object["key"]["name"] = f"{collection}"
            _json["result"].append(new_object)

        highlight = ui_highlight(increasing_number_of_objects_per_collection.long_collection_statistics, "file_name.txt", "verbosity")
        assert "Object displayed growth of 25.89" in highlight

    def test_no_highlight_for_high_number_of_growing_objects_per_collection(self):
        """
        Test object growth highlights is generated when the number of objects of the same type grows every collection
        """

        response = TestObject()
        response.is_success = True
        _json = copy.deepcopy(pytest.JSON)
        increasing_number_of_objects_per_collection = LongCollectionBundle(5)
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

        highlight = ui_highlight(increasing_number_of_objects_per_collection.long_collection_statistics, "file_name.txt", "verbosity")
        assert "Object of type HighlightsMP::Growing Object displayed negligible growth (2.52)" in highlight
