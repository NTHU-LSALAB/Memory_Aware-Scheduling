from functools import cmp_to_key
import json
from algorithms.algo_base import AlgoBase
from algorithms.heft_delay import HEFTDelay
from algorithms.heft_lookup import HEFTLookup
from algorithms.mem_first import MemFirst
from platforms.dep import Dep
from platforms.task import Task
from algorithms.heft import HEFT
from platforms.memory import Memory
import copy


class DAG:

    def get_algo(self, algo):
        if isinstance(algo, str):
            algo: AlgoBase = {
                'heft': HEFT(),
                'heft_delay': HEFTDelay(),
                'heft_lookup': HEFTLookup(),
                'mem_first': MemFirst()
            }[algo.lower()]
        return algo

    def read_input(self, filepath: str):
        self.tasks: list[Task] = []
        with open(filepath, 'r') as f:
            json_file = json.load(f)
            self.input = json_file["input"]
            for json_node in json_file["nodes"]:
                node = Task(
                    json_node["id"], json_node["costs"], json_node["output"], json_node.get("buffer", 10))
                self.tasks.append(node)

            def task_compare(task1: Task, task2: Task):
                return task1.id - task2.id
            self.tasks = sorted(self.tasks, key=cmp_to_key(task_compare))
            for json_edge in json_file["edges"]:
                source = self.tasks[json_edge["source"] - 1]
                target = self.tasks[json_edge["target"] - 1]
                new_edge = Dep(source, target, source.output)
                source.out_edges.append(new_edge)
                target.in_edges.append(new_edge)

    def schedule(self, algo, memory=None, algo_options: dict = {}) -> tuple[list[list[Task]], int]:
        algo = self.get_algo(algo)
        if memory:
            algo.memory = Memory(memory)
        tasks = copy.deepcopy(self.tasks)
        return algo.schedule(tasks, self.input, algo_options)

    def __repr__(self):
        string = '''DAG
---------------------------
'''
        for task in self.tasks:
            for edge in task.out_edges:
                string += f'{edge.source.id:>2} ---> {edge.target.id}\n'
        return string
