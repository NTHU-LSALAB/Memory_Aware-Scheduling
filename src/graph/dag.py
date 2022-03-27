from algorithms.algo_base import AlgoBase
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
                'heft_bf': HEFTBrutoForce()
            }[algo.lower()]
        return algo

    def read_input(self, filepath: str, memory=True):
        self.tasks = []
        with open(filepath, 'r') as f:
            [task_num] = map(int, next(f).split())
            self.input, self.output = map(int, next(f).split())
            self.tasks = []
            for tid in range(task_num):
                cost_table = [int(x) for x in next(f).split()]
                self.tasks.append(Node(tid+1, cost_table, 10))
            for sid in range(task_num-1):
                line = next(f).split()
                size = int(line[0])
                targets = list(map(int, line[1:]))
                for target in targets:
                    new_edge = Edge(self.tasks[sid],
                                    self.tasks[target-1], size)
                    self.tasks[sid].out_edges.append(new_edge)
                    self.tasks[target-1].in_edges.append(new_edge)

    def schedule(self, algo, memory = None) -> tuple[list[list[Node]], int]:
        algo = self.get_algo(algo)
        if memory:
            algo.memory = Memory(memory)
        tasks = copy.deepcopy(self.tasks)
        return algo.schedule(tasks, input=self.input, output=self.output)

    def __repr__(self):
        string = '''DAG
---------------------------
'''
        for task in self.tasks:
            for edge in task.out_edges:
                string += f'{edge.source.id}---{edge.weight}--->{edge.target.id}\n'
        return string
