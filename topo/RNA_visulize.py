import subprocess
import tempfile
import argparse
import re
from RNA import fold

def filter_internal_loops(graph_output):
    """
    Filter out internal loop nodes ('i') from the graph output and
    adjust edges to directly connect their neighbors.

    Parameters:
        graph_output (str): The raw graph text.

    Returns:
        str: The filtered graph text with 'i' nodes removed and edges adjusted.
    """
    lines = graph_output.splitlines()
    edge_lines = []
    node_connections = {}
    filtered_lines = []
    inside_graph = False  # To track if we're inside the `graph` block

    lines = [
        line for line in lines
        if not (line.strip().startswith("{node") and 'label="i' in line)
    ]

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith("graph G {"):
            inside_graph = True
            filtered_lines.append(line)
            continue

        if stripped_line == "}":
            inside_graph = False

        if inside_graph:
            edge_match = re.match(r'\s*(\S+)\s--\s(\S+);', line)
            if edge_match:
                node_a, node_b = edge_match.groups()

                # Check if either A or B contains 'i'
                if 'i' in node_a or 'i' in node_b:
                    # Record the connection for replacement
                    if 'i' in node_a:
                        node_connections.setdefault(node_a, []).append(node_b)
                    elif 'i' in node_b:
                        node_connections.setdefault(node_b, []).append(node_a)
                else:
                    # Keep lines without 'i' untouched
                    edge_lines.append((node_a, node_b))
            else:
                filtered_lines.append(line)
        else:
            filtered_lines.append(line)

    # Replace intermediate 'i' nodes with direct connections
    for intermediate, neighbors in node_connections.items():
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                edge_lines.append((neighbors[i], neighbors[j]))

    # Remove duplicates
    edge_lines = list(set(edge_lines))

    # Sort edges by node A's numeric part
    def sort_key(edge):
        a_numeric = int(re.search(r'\d+', edge[0]).group()) if re.search(r'\d+', edge[0]) else float('inf')
        b_numeric = int(re.search(r'\d+', edge[1]).group()) if re.search(r'\d+', edge[1]) else float('inf')
        return (a_numeric, b_numeric)

    edge_lines.sort(key=sort_key)

    # Format edges back into lines
    sorted_edge_lines = [f"    {a} -- {b};\n" for a, b in edge_lines]

    # Combine the processed output
    final_output = "\n".join(filtered_lines[:-1] + sorted_edge_lines + ["}"])
    return final_output

def generate_rna_graph(rna_sequence, output_image_path="graph.png", simple=False):
    """
    Generate a graph image from an RNA sequence.

    Parameters:
        rna_sequence (str): RNA sequence (A, U, G, C).
        output_image_path (str): Path to save the output PNG image.
        simple (bool): If True, internal loops (i) are excluded from the graph.
    """
    try:
        # Step 1: Generate structure string using ViennaRNA
        structure, mfe = fold(rna_sequence)
        print(f"RNA Structure (Dot-Bracket): {structure}")
        print(f"Minimum Free Energy: {mfe} kcal/mol")

        # Step 2: Write structure string to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dotbracket") as temp_file:
            temp_file.write(f">{rna_sequence}\n{structure}\n".encode('utf-8'))
            temp_file_path = temp_file.name

        # Step 3: Use examples/rnaConvert.py to generate graph text
        graph_output = subprocess.check_output(
            ["python3", "examples/rnaConvert.py", temp_file_path, "-T", "neato"],
            text=True
        )

        # Step 4: Optionally filter out internal loops (i)
        if simple:
            graph_output = filter_internal_loops(graph_output)
        
        graph_output_file = "graph_output.txt"
        with open(graph_output_file, "w", encoding="utf-8") as file:
            file.write(graph_output)
        print(f"Graph output saved to: {graph_output_file}")

        # Step 5: Generate PNG image using neato
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_image_file:
            subprocess.run(
                ["neato", "-Tpng", "-o", temp_image_file.name],
                input=graph_output,
                text=True
            )
            # Save the final image to the specified path
            subprocess.run(["cp", temp_image_file.name, output_image_path])

        print(f"Graph image saved at: {output_image_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate RNA graph from sequence.")
    parser.add_argument("rna_sequence", type=str, help="RNA sequence (A, U, G, C).")
    parser.add_argument("output_image_path", type=str, nargs="?", default="graph.png", help="Path to save the output PNG image (default: graph.png).")
    parser.add_argument("-s", "--simple", action="store_true", help="Exclude internal loops (i) from the graph.")
    args = parser.parse_args()

    generate_rna_graph(args.rna_sequence, args.output_image_path, simple=args.simple)
