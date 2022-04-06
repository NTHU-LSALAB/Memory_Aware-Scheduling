import json
from algorithms.algo_base import AlgoBase
from algorithms.heft_lookup import HEFTLookup
from graph.edge import Edge
from graph.node import Node
from algorithms.heft import HEFT
from algorithms.heft_delay import HEFTDelay
from algorithms.heft_bf import HEFTBrutoForce
from platforms.memory import Memory
import copy


class DAG:

    def get_algo(self, algo):
        if isinstance(algo, str):
            algo: AlgoBase = {
                'heft': HEFT(),
                'heft_delay': HEFTDelay(),
                'heft_bf': HEFTBrutoForce(),
                'heft_lookup': HEFTLookup()
            }[algo.lower()]
        return algo

    def read_input(self, filepath: str, memory=True):
        self.tasks: list[Node] = []
        with open(filepath, 'r') as f:
            json_file = json.load(f)
            self.input = json_file["input"]
            for json_node in json_file["nodes"]:
                node = Node(json_node["id"], json_node["costs"], json_node["output"], 10)
                self.tasks.append(node)
            for json_edge in json_file["edges"]:
                source = self.tasks[json_edge["from"] - 1]
                target = self.tasks[json_edge["to"] - 1]
                new_edge = Edge(source, target, source.output)
                source.out_edges.append(new_edge)
                target.in_edges.append(new_edge)

    def schedule(self, algo, memory=None) -> tuple[list[list[Node]], int]:
        algo = self.get_algo(algo)
        if memory:
            algo.memory = Memory(memory)
        tasks = copy.deepcopy(self.tasks)
        return algo.schedule(tasks, input=self.input)

    def __repr__(self):
        string = '''DAG
---------------------------
'''
        for task in self.tasks:
            for edge in task.out_edges:
                string += f'{edge.source.id}---{edge.weight}--->{edge.target.id}\n'
        return string
