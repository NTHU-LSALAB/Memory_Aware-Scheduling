from functools import cmp_to_key
import json
import sys
from typing import Union
from algorithms import get_scheduling_algorithm
from platforms.dep import Dep
from platforms.task import MTask
from platforms.task import Task
from platforms.memory import Memory
import copy
sys.setrecursionlimit(10000)


class DAG:

    def __init__(self, dag = None):
        if dag is not None:
            self.read_input(dag)

    # dag could be file name, dict object
    def read_input(self, dag: Union[str, dict], weight=True, format='default'):
        if isinstance(dag, str):
            dag = json.load(open(dag, 'r'))
       
        self.format = format
        self.tasks: list[Task] = []
        self.edges: list[Dep] = []
        self.input = dag.get("input", 0)
        for json_node in dag["nodes"]:
            node = Task(
                json_node["id"], json_node.get("costs", None), json_node.get("output"), json_node.get("buffer", 10))
            self.tasks.append(node)

        for task in dag.get('mTasks', []):
            task = MTask(task['id'], task['mId'],
                            task['type'], task.get('buffer', 10), task.get('io_type'))
            self.tasks.append(task)

        def task_compare(task1: Task, task2: Task):
            return task1.id - task2.id
        self.tasks = sorted(self.tasks, key=cmp_to_key(task_compare))
        for json_edge in dag["edges"]:
            source = self.tasks[json_edge["source"] - 1]
            target = self.tasks[json_edge["target"] - 1]
            new_edge = Dep(source, target, source.output if hasattr(source, 'output') else 0,
                            json_edge.get("weight", 0) if weight else 0)
            source.out_edges.append(new_edge)
            target.in_edges.append(new_edge)
            self.edges.append(new_edge)
            

    def schedule(self, algo, strategy=None, memory=None, algo_options: dict = {}) -> tuple[list[list[Task]], int]:
        self.algo = get_scheduling_algorithm(algo, strategy=strategy)
        snapshot = algo_options.get('snapshot', False)
        if memory:
            self.algo.memory = Memory(memory, snapshot)
        else:
            self.algo.memory = Memory(sys.maxsize, snapshot)
        tasks = copy.deepcopy(self.tasks)
        return self.algo.schedule(tasks, self.input, algo_options, format=self.format)

    def __repr__(self):
        string = '''DAG
---------------------------
'''
        for task in self.tasks:
            for edge in task.out_edges:
                string += f'{edge.source.id:>2} ---> {edge.target.id}\n'
        return string
