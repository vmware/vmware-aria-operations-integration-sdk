#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

import json
from collections import defaultdict
from json import JSONDecodeError

from vrealize_operations_integration_sdk.model import _get_object_id
from vrealize_operations_integration_sdk.validation.result import Result


class Cycle:
    def __init__(self, stack: list):
        # Note: stack is modified!
        current_node = stack.pop()
        cycle = [current_node]
        while len(stack) > 0 and stack[-1] != current_node:
            cycle.insert(0, stack.pop())
        self.cycle = cycle

    def __eq__(self, o: object) -> bool:
        if type(o) is Cycle:
            cycle_length = len(self.cycle)
            if len(o.cycle) != cycle_length:
                return False
            try:
                offset = o.cycle.index(self.cycle[0])
                for i in range(cycle_length):
                    if self.cycle[i] != o.cycle[(i + offset) % cycle_length]:
                        return False
                return True
            except ValueError:
                return False
        return False

    def __hash__(self):
        cycle_length = len(self.cycle)
        hash_values = [hash(node) for node in self.cycle]
        min_value = min(hash_values)
        offset = hash_values.index(min_value)
        string = ""
        for i in range(cycle_length):
            string += repr(self.cycle[(i + offset) % cycle_length]) + ":"
        return hash(string)

    def __repr__(self):
        if len(self.cycle) > 0:
            return str(self.cycle[-1]) + " -> " + " -> ".join(str(node) for node in self.cycle)
        return ""


class Graph:
    def __init__(self, nodes: set, adjacency_map: dict):
        self.nodes = nodes
        self.adjacency_map = adjacency_map

    def get_cycles(self) -> set[Cycle]:
        cycles = set()
        if len(self.nodes) == 0:
            return cycles
        state = defaultdict(lambda: "UNVISITED")
        for node in self.nodes:
            if state[node] == "UNVISITED":
                stack = [node]
                state[node] = "VISITED"
                cycles.update(self._get_cycle(stack, state))
        return cycles

    def _get_cycle(self, stack: list, state: dict) -> set[Cycle]:
        cycles = set()
        current_node = stack[-1]
        for adj_node in self.adjacency_map.get(current_node, []):
            if state[adj_node] == "VISITED":
                # Construct a new stack, so we don't care if it's modified
                cycle = Cycle(stack + [adj_node])
                cycles.add(cycle)
            elif state[adj_node] == "UNVISITED":
                stack.append(adj_node)
                state[adj_node] = "VISITED"
                cycles.update(self._get_cycle(stack, state))
        state[current_node] = "DONE"
        stack.pop()
        return cycles


def validate_relationships(project, request, response):
    result = Result()
    try:
        if not response.is_success:
            result.with_error(f"Unable to validate relationships. The '{request.url}' endpoint response was: "
                              f"{response.status_code} {response.reason_phrase}")
            return result

        results = json.loads(response.text)

        # NOTE: in cases where the adapter crashes (500) results is a string, otherwise is a regular response
        if (type(results) is not dict) or ("relationships" not in results):
            result.with_error("No collection result was found.")
            return result
        else:
            nodes = set()
            adjacency_map = defaultdict(lambda: set())

            for rel in results.get("relationships", []):
                parent = _get_object_id(rel.get("parent"))
                nodes.add(parent)
                children = rel.get("children", [])
                for child in children:
                    child = _get_object_id(child)
                    nodes.add(child)
                    # We are looking for cycles in a directed graph, so add parent-child relationships but
                    # not child-parent relationships to adjacency map
                    adjacency_map[parent].add(child)
            graph = Graph(nodes, adjacency_map)
            cycles = graph.get_cycles()
            for cycle in cycles:
                result.with_error(f"Found relationship cycle: {cycle}")

    except JSONDecodeError as d:
        result.with_error(f"Unable to validate relationships. Returned result is not valid json: "
                          f"'{repr(response.text)}' Error: '{d}'")
    except Exception as e:
        result.with_error(f"Unable to validate relationships: '{e}'")
    return result
