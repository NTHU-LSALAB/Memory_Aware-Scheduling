from itertools import count
import json
import os
from matplotlib import pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

with open('samples/sample.3.json', 'r') as f:
    plt.figure(figsize=(3.8,4), dpi=1000)
    json_file = json.load(f)
    edge_list = []
    node_list = []
    node_color = []
    node_attrs = {}
    reserved = [1, 2, 3, 4]
    deps = []
    reserving = None
    successors = []
    failed = [6]
    for json_node in json_file['nodes']:
        node_attrs[json_node['id']] = '(' + \
            str(json_node.get('buffer', 10))+', '+str(json_node['output']) + ')'
        node_list.append(json_node['id'])
        tid = json_node['id']
        if tid in reserved:
            node_color.append('#E0E0E0')
        elif tid in deps:
            node_color.append('#E0E0E0')
        elif tid == reserving:
            node_color.append('#CCE5FF')
        elif tid in successors:
            node_color.append('#E5FFCC')
        elif tid in failed:
            node_color.append('#FFCCCC')
        else:
            node_color.append('#FAFEFF')
    for json_edge in json_file["edges"]:
        edge_list.append((json_edge["source"], json_edge["target"], {
                         "weight": json_edge.get('weight', 0)}))

    graph = nx.from_edgelist(edge_list, create_using=nx.DiGraph)
    pos = {1: (0, 3), 2: (-0.5, 2), 3: (0, 2), 4: (0.5, 2),
           5: (-0.25, 1), 6: (0.25, 1), 7: (0, 0)}
    node_pos = {}
    for node, coords in pos.items():
        node_pos[node] = (coords[0] + 0.18, coords[1])
    # pos = {1: (0, 3), 2: (-1, 2), 3: (-0.5, 2), 4: (0, 2), 5: (0.5, 2),
    #        6: (1, 2), 7: (-0.75, 1), 8: (0, 1), 9: (0.75, 1), 10: (0, 0)}
    # pos = graphviz_layout(graph, prog='dot')
    nx.set_node_attributes(graph, dict(
        zip(graph.nodes(), node_color)), 'color')
    labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw(graph,
            pos,
            with_labels=True,
            node_size=1000,
            node_color=[node[1]['color']
                        for node in graph.nodes(data=True)],
            width=1,
            edgecolors='black',
            )
    nx.draw_networkx_labels(graph, node_pos, node_attrs, font_size=8)
    # nx.draw_networkx_edge_labels(
    #     graph, pos, edge_labels=labels,
    #     bbox=dict(alpha=0), rotate=False)
    x_values, y_values = zip(*pos.values())
    x_max = max(x_values)
    x_min = min(x_values)
    x_margin = (x_max - x_min) * 0.3
    plt.xlim(x_min - x_margin/2.5, x_max + x_margin)
    if 'latex' in os.environ:
        plt.savefig('tmp.eps', format="eps", dpi=1200,
                    bbox_inches="tight", transparent=True)
    else:
        plt.savefig('tmp.png')
