from app.ml.graph_fraud import (
    UserLinkEdge,
    build_user_link_graph,
    detect_communities,
    flag_suspicious_communities,
)


def test_build_graph_from_edges():
    edges = [UserLinkEdge("u1", "u2", 1.0), UserLinkEdge("u2", "u3", 1.0)]
    graph = build_user_link_graph(edges)
    assert set(graph.nodes) == {"u1", "u2", "u3"}


def test_detect_communities_groups_a_tight_ring_together():
    # u1-u5 all densely share a device (a ring); u10-u11 are a separate,
    # unrelated pair.
    ring_edges = [UserLinkEdge(f"u{i}", f"u{j}", 5.0) for i in range(1, 6) for j in range(i + 1, 6)]
    other_edge = [UserLinkEdge("u10", "u11", 1.0)]
    graph = build_user_link_graph(ring_edges + other_edge)

    communities = detect_communities(graph)
    ring_community = next(c for c in communities if "u1" in c)
    assert {"u1", "u2", "u3", "u4", "u5"} <= ring_community
    assert "u10" not in ring_community


def test_flag_suspicious_communities_flags_large_concentrated_group():
    ring_edges = [UserLinkEdge(f"u{i}", f"u{j}", 5.0) for i in range(1, 7) for j in range(i + 1, 7)]
    graph = build_user_link_graph(ring_edges)
    communities = detect_communities(graph)

    # All 6 ring users only ever reviewed the same single entity.
    touches = {f"u{i}": {"entity-x"} for i in range(1, 7)}
    flagged = flag_suspicious_communities(communities, user_entity_touches=touches, min_size=5)

    assert len(flagged) == 1
    assert flagged[0].size == 6


def test_flag_suspicious_communities_ignores_diverse_large_group():
    ring_edges = [UserLinkEdge(f"u{i}", f"u{j}", 1.0) for i in range(1, 7) for j in range(i + 1, 7)]
    graph = build_user_link_graph(ring_edges)
    communities = detect_communities(graph)

    # Same size community, but each user touched a different entity ->
    # spread across many entities, not concentrated -> not flagged.
    touches = {f"u{i}": {f"entity-{i}"} for i in range(1, 7)}
    flagged = flag_suspicious_communities(communities, user_entity_touches=touches, min_size=5)

    assert flagged == []
