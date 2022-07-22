import json
from matplotlib import pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

with open('samples/sample.3.json', 'r') as f:
    json_file = json.load(f)
    edge_list = []
    node_attrs = {}
    for json_node in json_file['nodes']:
        node_attrs[json_node['id']] = '(' + \
            str(json_node.get('buffer', 10))+', '+str(json_node['output']) + ')'
    for json_edge in json_file["edges"]:
        edge_list.append((json_edge["source"], json_edge["target"], {
                         "weight": json_edge.get('weight', 0)}))

    graph = nx.from_edgelist(edge_list, create_using=nx.DiGraph)
    pos = {1: (0, 3), 2: (-0.5, 2), 3: (0, 2), 4: (0.5, 2),
           5: (-0.25, 1), 6: (0.25, 1), 7: (0, 0)}
    node_pos = {}
    for node, coords in pos.items():
        node_pos[node] = (coords[0] + 0.13, coords[1])
    # pos = {1: (0, 3), 2: (-1, 2), 3: (-0.5, 2), 4: (0, 2), 5: (0.5, 2),
    #        6: (1, 2), 7: (-0.75, 1), 8: (0, 1), 9: (0.75, 1), 10: (0, 0)}
    # pos = graphviz_layout(graph, prog='dot')
    labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw(graph,
            pos,
            with_labels=True,
            node_size=1000,
            node_color="white",
            width=0.8,
            edgecolors='black',
            )
    nx.draw_networkx_labels(graph, node_pos, node_attrs, font_size=8)
    # nx.draw_networkx_edge_labels(
    #     graph, pos, edge_labels=labels,
    #     bbox=dict(alpha=0), rotate=False)
    x_values, y_values = zip(*pos.values())
    x_max = max(x_values)
    x_min = min(x_values)
    x_margin = (x_max - x_min) * 0.5
    plt.xlim(x_min - x_margin, x_max + x_margin)
    plt.savefig('tmp.png')
