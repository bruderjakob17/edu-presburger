import pydot
from collections import defaultdict


def relabel_and_aggregate(dot_input: str,
                          states: [int],
                          n: int):
    # Parse the input DOT graph
    graphs = pydot.graph_from_dot_data(dot_input)
    if not graphs:
        raise ValueError("Invalid DOT input")

    graph = graphs[0]

    # Collect transitions grouped by (src, dst)
    transitions = defaultdict(list)
    for edge in graph.get_edges():
        src = edge.get_source()
        dst = edge.get_destination()
        label = edge.get_label().strip('"') if edge.get_label() else ''
        transitions[(src, dst)].append(label)

    # Remove all original edges
    for edge in graph.get_edges():
        graph.del_edge(edge.get_source(), edge.get_destination())

    # Add merged transitions
    for (src, dst), labels in transitions.items():
        merged_label = ",".join(sorted(set(labels)))
        edge = pydot.Edge(src, dst, label=merged_label)
        graph.add_edge(edge)

    return graph.to_string()

def int_to_lsbf(n, width):
    return tuple((n >> i) & 1 for i in range(width))

def decode(k):
    if k % 2 == 0:
        return k // 2
    else:
        return (k-1) // -2