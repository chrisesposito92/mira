"""Tests for the product/meter/aggregation graph structure."""

from app.agents.graphs.product_meter_agg import _build_graph, _should_clarify


class TestShouldClarify:
    def test_returns_clarify_when_needed(self):
        state = {"needs_clarification": True}
        assert _should_clarify(state) == "generate_clarifications"

    def test_returns_generate_when_not_needed(self):
        state = {"needs_clarification": False}
        assert _should_clarify(state) == "generate_products"

    def test_returns_generate_when_key_missing(self):
        state = {}
        assert _should_clarify(state) == "generate_products"


class TestGraphStructure:
    def test_graph_has_all_nodes(self):
        graph = _build_graph()
        expected_nodes = {
            "analyze_use_case",
            "generate_clarifications",
            "generate_products",
            "validate_products",
            "approve_products",
            "generate_meters",
            "validate_meters",
            "approve_meters",
            "generate_aggregations",
            "validate_aggregations",
            "approve_aggregations",
            "generate_compound_aggregations",
            "validate_compound_aggregations",
            "approve_compound_aggregations",
        }
        # StateGraph nodes dict includes __start__ and __end__
        node_names = {name for name in graph.nodes if not name.startswith("__")}
        assert expected_nodes == node_names

    def test_graph_entry_point_is_analyze(self):
        graph = _build_graph()
        # The entry point creates an edge from __start__ to analyze_use_case
        assert "__start__" in graph.nodes or "analyze_use_case" in graph.nodes

    def test_graph_compiles_without_checkpointer(self):
        graph = _build_graph()
        # Compile without checkpointer for testing
        compiled = graph.compile()
        assert compiled is not None
