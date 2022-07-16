import json
from matplotlib import pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

with open('samples/sample.1.json', 'r') as f:
    json_file = json.load(f)
    node_list = []
    edge_list = []
    for json_edge in json_file["nodes"]:
        node_list.append(json_edge["id"])
    for json_edge in json_file["edges"]:
        edge_list.append((json_edge["source"], json_edge["target"], {
                         "weight": json_edge.get('weight', 0)}))

    graph = nx.from_edgelist(edge_list, create_using=nx.DiGraph)
    pos = {1: (0, 3), 2: (-1, 2), 3: (-0.5, 2), 4: (0, 2), 5: (0.5, 2),
           6: (1, 2), 7: (-0.75, 1), 8: (0, 1), 9: (0.75, 1), 10: (0, 0)}
    labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw(graph,
            pos,
            with_labels=True,
            node_size=1000,
            node_color="white",
            width=0.8,
            edgecolors='black',
            )
    nx.draw_networkx_edge_labels(
        graph, pos, edge_labels=labels,
        bbox=dict(alpha=0), rotate=False)
    x_values, y_values = zip(*pos.values())
    x_max = max(x_values)
    x_min = min(x_values)
    x_margin = (x_max - x_min) * 0.3
    plt.xlim(x_min - x_margin, x_max + x_margin)
    plt.savefig('tmp.png')
