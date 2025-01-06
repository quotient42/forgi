import networkx as nx
import re
import argparse

def parse_graph_with_bases(file_path):
    """
    Parse a graph definition from a text file into a NetworkX graph and extract node base counts.

    Parameters:
        file_path (str): Path to the text file containing the graph definition.

    Returns:
        tuple: Graph object (nx.Graph) and a dictionary of base counts for each node.
    """
    G = nx.Graph()
    base_counts = {}

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Patterns for edge and node lines
    edge_pattern = re.compile(r"\s*(\S+)\s--\s(\S+);")
    node_pattern = re.compile(r'label=".*?\((\d+)\)"]\s+(\S+)};')

    for line in lines:
        # Match edges
        edge_match = edge_pattern.match(line)
        if edge_match:
            node_a, node_b = edge_match.groups()
            G.add_edge(node_a.strip(), node_b.strip())

        # Match nodes with base counts
        node_match = node_pattern.search(line)
        if node_match:
            base_count, node = node_match.groups()
            base_counts[node.strip()] = int(base_count)

    return G, base_counts

def find_longest_path_by_edges(graph):
    """
    Find the longest path in the graph based on the number of edges.

    Parameters:
        graph (nx.Graph): The input graph.

    Returns:
        tuple: Longest path (list of nodes) and its length in edges.
    """
    longest_path = []
    max_length = 0

    for node in graph.nodes:
        for target in graph.nodes:
            if node != target:
                try:
                    path = nx.shortest_path(graph, source=node, target=target, weight=None, method="dijkstra")
                    if len(path) > max_length:
                        longest_path = path
                        max_length = len(path)
                except nx.NetworkXNoPath:
                    continue

    return longest_path, max_length - 1  # Subtract 1 to count edges

def find_longest_path_by_bases(graph, base_counts):
    """
    Find the longest path in the graph based on the total number of bases.

    Parameters:
        graph (nx.Graph): The input graph.
        base_counts (dict): A dictionary mapping nodes to their base counts.

    Returns:
        tuple: Longest path (list of nodes) and its total base count.
    """
    longest_path = []
    max_bases = 0

    for node in graph.nodes:
        for target in graph.nodes:
            if node != target:
                try:
                    path = nx.shortest_path(graph, source=node, target=target, weight=None, method="dijkstra")
                    base_sum = sum(base_counts.get(n, 0) for n in path)
                    if base_sum > max_bases:
                        longest_path = path
                        max_bases = base_sum
                except nx.NetworkXNoPath:
                    continue

    return longest_path, max_bases

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find the longest path in a graph.")
    parser.add_argument("input_file", type=str, help="Path to the graph definition file.")
    parser.add_argument("-b", "--base", action="store_true", help="Use base counts to determine the longest path.")
    args = parser.parse_args()

    # Parse the graph and base counts
    G, base_counts = parse_graph_with_bases(args.input_file)

    if args.base:
        # Find the longest path by base counts
        longest_path, total_bases = find_longest_path_by_bases(G, base_counts)
        print(f"{longest_path[0]} ~ {longest_path[-1]}")
        print(f"Longest Path: {longest_path}")
        print(f"Total Base Count: {total_bases}")
    else:
        # Find the longest path by edges
        longest_path, length = find_longest_path_by_edges(G)
        print(f"{longest_path[0]} ~ {longest_path[-1]}")
        print(f"Longest Path: {longest_path}")
        print(f"Total Node Count: {length}")
    
