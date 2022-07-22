import json
from matplotlib import pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

with open('samples/sample.sbac.json', 'r') as f:
    json_file = json.load(f)
    edge_list = []
    node_attrs = {}
    for json_edge in json_file["edges"]:
        edge_list.append((json_edge["source"], json_edge["target"], {
                         "weight": json_edge.get('weight', 0)}))

    graph = nx.from_edgelist(edge_list, create_using=nx.DiGraph)
    # pos = graphviz_layout(graph, prog='dot', root=1000)
    # labels = nx.get_edge_attributes(graph, 'weight')
    A = nx.nx_agraph.to_agraph(graph)
    A.layout(prog='dot')            # neato layout

    A.draw('test.png',args='-Gfont_size=1', prog='dot' )  
    # nx.draw(graph,
    #         pos,
    #         with_labels=True,
    #         node_size=500,
    #         node_color="white",
    #         width=0.8,
    #         edgecolors='black',
    #         )
    # plt.figure(figsize=(32, 32))
    # plt.savefig('tmp.png')
