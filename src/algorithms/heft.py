import sys
from algorithms.algo_base import AlgoBase
from functools import cmp_to_key
import numpy as np

from platforms.memory import Memory
from platforms.task import Task


class HEFT(AlgoBase):

    def schedule(self, tasks: list[Task], input, options={}) -> tuple[list[list[Task]], int]:
        # print('HEFT')
        self.memory = Memory(sys.maxsize)
        makespan = 0
        entry_task = next(
            (task for task in tasks if len(task.in_edges) == 0), None)
        exit_task = next(
            (task for task in tasks if len(task.out_edges) == 0), None)

        if entry_task is None or exit_task is None:
            raise ValueError('No entry or exit node')

        calculate_priority(entry_task)

        sorted_tasks = sorted(tasks, key=cmp_to_key(task_compare))
        self.priority_list = list(map(lambda task: task.id, sorted_tasks))
        schedule: list[list[Task]] = [[]
                                      for _ in range(len(entry_task.cost_table))]

        for task in sorted_tasks:
            ast, aft, pid = find_processor(task, schedule)

            # allocate input tensor
            if task is entry_task:
                self.memory.fit(
                    input, [ast, aft], task, can_delay=False)
            # allocate output tensor
            if task is exit_task:
                self.memory.fit(
                    task.output, [ast, aft], task, can_delay=False)
            else:
                # allocate task's output tensor
                self.memory.fit(task.out_edges[0].size, [
                    ast, Memory.DEADLINE], task, final=False, can_delay=False)
            # allocate internal buffer
            self.memory.fit(
                task.buffer_size, [ast, aft], task, can_delay=False)
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
                        until = max(until, aft)
                        self.memory.free_tensor(in_edge.source, until)
            task.procId = pid + 1
            task.ast = ast
            task.aft = aft
            schedule[pid].append(task)
            if task.aft > makespan:
                makespan = task.aft

        return schedule, makespan, self.memory.max()

    def print_priority(self, entry_node: Task):
        print('''UPPER RANKS
---------------------------
Task    Rank
---------------------------''')
        self.bfs(entry_node, op=lambda task: print(
            f'{task.id}       {round(task.priority, 4)}'))


def task_compare(task1: Task, task2: Task):
    return task2.priority - task1.priority


def calculate_priority(task: Task):
    if task.priority:
        return task.priority
    max = 0
    for edge in task.out_edges:
        cost = edge.weight + calculate_priority(edge.target)
        if cost > max:
            max = cost
    task.priority = task.cost_avg + max
    return task.priority


def find_processor(task: Task, schedule):
    min_eft_procId = np.argmin(task.cost_table)
    min_eft = task.cost_table[min_eft_procId] if task.is_entry(
    ) else sys.maxsize
    # Calculate start time
    selected_ast = est = 0 if task.is_entry() else max(
        [edge.source.aft if edge.source.aft else 0 for edge in task.in_edges])
    # Choose a processor
    for pid, cost in enumerate(task.cost_table):
        proc_est = schedule[pid][-1].aft if len(
            schedule[pid]) > 0 else est

        # Check if current task and its parents are on the same processor
        undones = []
        for in_edge in task.in_edges:
            # parent not scheduled yet, cannot schedule this task
            if not in_edge.source.procId:
                undones.append(in_edge.source)
                continue
            if in_edge.source.procId-1 != pid:
                proc_est = max(in_edge.source.aft +
                               in_edge.weight, proc_est)
        if undones:
            raise Exception(undones)
        eft = proc_est + cost
        if eft < min_eft:
            selected_ast = proc_est
            min_eft = eft
            min_eft_procId = pid

    return selected_ast, min_eft, min_eft_procId
