import sys
from algorithms.algo_base import AlgoBase
from graph.node import Node
from functools import cmp_to_key
import numpy as np

from platforms.memory import Memory


def task_compare(task1: Node, task2: Node):
    return task2.rank - task1.rank


class HEFT(AlgoBase):

    def schedule(self, tasks: list[Node], input, options = {}) -> tuple[list[list[Node]], int]:
        # print('HEFT')
        self.memory = Memory(sys.maxsize)
        makespan = 0
        entry_task = next(
            (task for task in tasks if len(task.in_edges) == 0), None)
        exit_task = next(
            (task for task in tasks if len(task.out_edges) == 0), None)

        if entry_task is None or exit_task is None:
            raise ValueError('No entry or exit node')

        self.calculate_rank(entry_task)
        sorted_tasks = sorted(tasks, key=cmp_to_key(task_compare))
        proc_schedule: list[list[Node]] = [[]
                                           for _ in range(len(entry_task.cost_table))]

        for task in sorted_tasks:
            min_eft_proc = np.argmin(task.cost_table)
            min_eft = task.cost_table[min_eft_proc] if task is entry_task else sys.maxsize
            selected_ast = est = 0 if task is entry_task else max(
                [edge.source.aft for edge in task.in_edges])
            for pid, cost in enumerate(task.cost_table):
                proc_est = proc_schedule[pid][-1].aft if len(
                    proc_schedule[pid]) > 0 else est
                for in_edge in task.in_edges:
                    if in_edge.source.procId-1 != pid:
                        proc_est = max(in_edge.source.aft +
                                       in_edge.weight, proc_est)
                eft = proc_est + cost
                if eft < min_eft:
                    selected_ast = proc_est
                    min_eft = eft
                    min_eft_proc = pid

            # allocate input tensor
            if task is entry_task:
                self.memory.first_fit(
                    input, [selected_ast, min_eft], task, can_delay=False)
            # allocate output tensor
            if task is exit_task:
                self.memory.first_fit(
                    task.output, [selected_ast, min_eft], task, can_delay=False)
            else:
                # allocate task's output tensor
                self.memory.first_fit(task.out_edges[0].size, [
                    selected_ast, Memory.DEADLINE], task, final=False, can_delay=False)
            # allocate internal buffer
            self.memory.first_fit(
                task.buffer_size, [selected_ast, min_eft], task, can_delay=False)
            # free input tensors
            if task is not entry_task:
                # check if inputs can be free
                for in_edge in task.in_edges:
                    last_use = True
                    until = -1
                    for out_edge in in_edge.source.out_edges:
                        if out_edge.target is task:
                            continue
                        if out_edge.target.procId is None:  # not allocate yet
                            last_use = False
                            break
                        until = max(until, out_edge.target.aft)
                    if last_use:
                        until = max(until, min_eft)
                        self.memory.free_tensor(in_edge.source, until)
            task.procId = min_eft_proc + 1
            task.ast = selected_ast
            task.aft = min_eft
            proc_schedule[min_eft_proc].append(task)
            if task.aft > makespan:
                makespan = task.aft

        return proc_schedule, makespan, self.memory.max()

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
