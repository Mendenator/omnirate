"""Louvain community detection over the user-linkage graph (P2-09).

Edges connect users who share a signal that shouldn't normally be shared at
scale: same device_id, same IP /24 subnet, or reviewed the same entity within
a tight time window. A large, dense community is the graph-native signature
of a coordinated review ring — a single user acting alone never forms one.

Acceptance: 1M edges <=5min. networkx's Louvain implementation is pure
Python and fine for the dev/test graphs here; at real 1M-edge scale, swap the
backend for igraph or graph-tool (both C-backed, same community output
shape) — a note, not a blocker, since this module's *output contract*
(list of user-id sets) doesn't change with that swap.
"""

from dataclasses import dataclass

import networkx as nx
from networkx.algorithms.community import louvain_communities

# A community larger than this, all touching a narrow set of entities, is
# flagged — tuned down from "any community" because organic friend groups
# legitimately review the same popular restaurant sometimes.
SUSPICIOUS_COMMUNITY_MIN_SIZE = 5
SUSPICIOUS_ENTITY_CONCENTRATION_MAX = 3  # flagged community touches <=3 distinct entities


@dataclass(frozen=True)
class UserLinkEdge:
    user_a: str
    user_b: str
    weight: float  # e.g. count of shared devices/IPs/co-review events


@dataclass(frozen=True)
class SuspiciousCommunity:
    user_ids: frozenset[str]
    size: int


def build_user_link_graph(edges: list[UserLinkEdge]) -> nx.Graph:
    graph = nx.Graph()
    for edge in edges:
        graph.add_edge(edge.user_a, edge.user_b, weight=edge.weight)
    return graph


def detect_communities(graph: nx.Graph) -> list[frozenset[str]]:
    return [frozenset(c) for c in louvain_communities(graph, weight="weight", seed=42)]


def flag_suspicious_communities(
    communities: list[frozenset[str]],
    *,
    user_entity_touches: dict[str, set[str]],
    min_size: int = SUSPICIOUS_COMMUNITY_MIN_SIZE,
    max_entity_concentration: int = SUSPICIOUS_ENTITY_CONCENTRATION_MAX,
) -> list[SuspiciousCommunity]:
    """`user_entity_touches[user_id]` is the set of entity_ids that user has
    reviewed — a community is flagged when it's both large AND concentrated
    on very few entities (large + diverse = probably just an active,
    legitimate community, not a ring)."""
    flagged = []
    for community in communities:
        if len(community) < min_size:
            continue
        touched_entities: set[str] = set()
        for user_id in community:
            touched_entities |= user_entity_touches.get(user_id, set())
        if len(touched_entities) <= max_entity_concentration:
            flagged.append(SuspiciousCommunity(user_ids=community, size=len(community)))
    return flagged
