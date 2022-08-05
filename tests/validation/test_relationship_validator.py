#  Copyright 2022 VMware, Inc.
#  SPDX-License-Identifier: Apache-2.0

from vrealize_operations_integration_sdk.validation.relationship_validator import Graph, Cycle


def test_no_nodes():
    nodes = set()
    adj = {}
    graph = Graph(nodes, adj)
    assert bool(graph.get_cycles()) is False


def test_no_cycle_1():
    # This contains a cycle if the graph is undirected.
    # Our graph is directed, so get_cycles should be falsy.
    nodes = {1, 2, 3}
    adj = {1: [2, 3], 2: [3]}
    graph = Graph(nodes, adj)
    assert bool(graph.get_cycles()) is False


def test_no_cycle_2():
    # This is the same test as (1), but with ordering switched
    nodes = {1, 2, 3}
    adj = {1: [3, 2], 2: [3]}
    graph = Graph(nodes, adj)
    assert bool(graph.get_cycles()) is False


def test_has_cycle_1():
    # Simple graph where nodes are parents of each other
    nodes = {1, 2}
    adj = {1: [2], 2: [1]}
    graph = Graph(nodes, adj)
    print(graph.get_cycles())
    assert graph.get_cycles() == {Cycle([1, 2])}


def test_has_cycle_2():
    # This graph contains a node that is a parent to itself
    nodes = {1, 2, 3}
    adj = {1: [2, 3], 2: [3], 3: [3]}
    graph = Graph(nodes, adj)
    print(graph.get_cycles())
    assert graph.get_cycles() == {Cycle([3])}


def test_has_cycle_3():
    # More complex graph with a cycle that does not contain the first node.
    nodes = {1, 2, 3, 4, 5}
    adj = {1: [2, 3], 2: [3], 3: [4], 4: [5], 5: [2]}
    graph = Graph(nodes, adj)
    print(graph.get_cycles())
    assert graph.get_cycles() == {Cycle([2, 3, 4, 5])}


def test_has_cycle_4():
    # More complex graph with multiple cycles
    nodes = {1, 2, 3, 4, 5, 6}
    adj = {1: [2], 2: [3], 3: [5], 5: [4], 4: [1, 2, 6], 6: [5]}
    graph = Graph(nodes, adj)
    print(graph.get_cycles())
    assert graph.get_cycles() == {Cycle([1, 2, 3, 5, 4]), Cycle([2, 3, 5, 4]), Cycle([4, 6, 5])}


def test_cycle_equality_1():
    c1 = Cycle([1, 2])
    c2 = Cycle([1, 2])
    assert c1 == c2
    assert hash(c1) == hash(c2)


def test_cycle_equality_2():
    c1 = Cycle([1, 2])
    c2 = Cycle([2, 1])
    assert c1 == c2
    assert hash(c1) == hash(c2)


def test_cycle_equality_3():
    # These are the same cycles, starting from different nodes
    c1 = Cycle([1, 2, 3, 4])
    c2 = Cycle([3, 4, 1, 2])
    assert c1 == c2
    assert hash(c1) == hash(c2)


def test_cycle_inequality_1():
    c1 = Cycle([1, 2, 3, 4])
    c2 = Cycle([1, 2, 3])
    assert c1 != c2
    print(hash(c1))
    print(hash(c2))
    assert hash(c1) != hash(c2)


def test_cycle_inequality_2():
    # Note: These are not the same, because our graphs are directed
    # (one is clockwise, the other is counterclockwise)
    c1 = Cycle([1, 2, 3])
    c2 = Cycle([1, 3, 2])
    assert c1 != c2
    print(hash(c1))
    print(hash(c2))
    assert hash(c1) != hash(c2)


def test_cycle_inequality_3():
    c1 = Cycle([1, 2, 4])
    c2 = Cycle([1, 2, 3])
    assert c1 != c2
    print(hash(c1))
    print(hash(c2))
    assert hash(c1) != hash(c2)


def test_cycle_inequality_4():
    c1 = Cycle([1, 2, 3, 4])
    c2 = Cycle([4, 3, 2, 1])
    assert c1 != c2
    print(hash(c1))
    print(hash(c2))
    assert hash(c1) != hash(c2)
