from functools import cmp_to_key
import json
import sys
from typing import Union
from algorithms.algo_base import AlgoBase
from algorithms.cpop import CPOP
from algorithms.cpop_delay import CPOPDelay
from algorithms.cpop_lookup import CPOPLookup
from algorithms.heft_delay import HEFTDelay
from algorithms.heft_lookup import HEFTLookup
from algorithms.ippts import IPPTS
from algorithms.ippts_lookup import IPPTSLookup
from algorithms.mem_first import MemFirst
from algorithms.sbac import SBAC
from platforms.dep import Dep
from platforms.task import MTask
from platforms.task import Task
from algorithms.heft import HEFT
from platforms.memory import Memory
import copy
sys.setrecursionlimit(10000)


class DAG:

    def __init__(self, dag = None):
        if dag is not None:
            self.read_input(dag)
    def get_algo(self, algo):
        if isinstance(algo, str):
            algo: AlgoBase = {
                'heft': HEFT(),
                'heft_delay': HEFTDelay(),
                'heft_lookup': HEFTLookup(),
                'cpop': CPOP(),
                'cpop_delay': CPOPDelay(),
                'cpop_lookup': CPOPLookup(),
                'ippts': IPPTS(),
                'ippts_lookup': IPPTSLookup(),
                'mem_first': MemFirst(),
                'sbac': SBAC()
            }[algo.lower()]
        return algo

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
            

    def schedule(self, algo, memory=None, algo_options: dict = {}) -> tuple[list[list[Task]], int]:
        self.algo = self.get_algo(algo)
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
