import sys
from algorithms.algo_base import AlgoBase
from graph.node import Node
from functools import cmp_to_key
import numpy as np


def task_compare(task1: Node, task2: Node):
    return task2.rank - task1.rank


class HEFT(AlgoBase):

    def schedule(self, tasks: list[Node], input, output) -> tuple[list[list[Node]], int]:
        print('HEFT')
        makespan = 0
        entry_task = next(
            (task for task in tasks if len(task.in_edges) == 0), None)
        if entry_task is None:
            raise ValueError

        self.calculate_rank(entry_task)
        sorted_tasks = sorted(tasks, key=cmp_to_key(task_compare))
        proc_schedule: list[list[Node]] = [[]
                                           for i in range(len(entry_task.cost_table))]

        for task in sorted_tasks:
            min_EFT_proc = np.argmin(task.cost_table)
            min_EFT = task.cost_table[min_EFT_proc] if task is entry_task else sys.maxsize
            selected_AST = EST = 0 if task is entry_task else max(
                [edge.source.aft for edge in task.in_edges])
            for pid, cost in enumerate(task.cost_table):
                proc_EST = proc_schedule[pid][-1].aft if len(
                    proc_schedule[pid]) > 0 else EST
                for in_edge in task.in_edges:
                    if in_edge.source.procId-1 != pid:
                        proc_EST = max(in_edge.source.aft +
                                       in_edge.weight, proc_EST)
                EFT = proc_EST + cost
                if EFT < min_EFT:
                    selected_AST = proc_EST
                    min_EFT = EFT
                    min_EFT_proc = pid
            task.procId = min_EFT_proc + 1
            task.ast = selected_AST
            task.aft = min_EFT
            proc_schedule[min_EFT_proc].append(task)
            if task.aft > makespan:
                makespan = task.aft

        return proc_schedule, makespan

    def calculate_rank(self, node: Node):
        if node.rank:
            return node.rank
        max = 0
        for edge in node.out_edges:
            cost = edge.weight + self.calculate_rank(edge.target)
            if cost > max:
                max = cost
        node.rank = node.cost_avg + max
        return node.rank

    def print_rank(self, entry_node: Node):
        print('''UPPER RANKS
---------------------------
Task    Rank
---------------------------''')
        self.bfs(entry_node, op=lambda task: print(
            f'{task.id}       {round(task.rank, 4)}'))
