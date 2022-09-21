from heapq import heapify, heappop, heappush
import sys
from typing import Union
from algorithms.algo_base import AlgoBase
import numpy as np
from lib.utils import ssse

from platforms.memory import Memory
from platforms.task import Task, MTask


class HEFT(AlgoBase):

    def schedule(self, tasks: list[Task], input, options={}, format='default') -> tuple[list[list[Task]], int]:
        # print('HEFT')
        makespan = 0
        task_count = len(
            list(filter(lambda task: isinstance(task, Task), tasks)))
        entry_task, _ = ssse(tasks)

        calculate_priority(entry_task)

        schedule: list[list[Task]] = [[]
                                      for _ in range(len(entry_task.cost_table))]

        task_heap = [entry_task]
        heapify(task_heap)

        while len(task_heap):
            task = heappop(task_heap)

            if isinstance(task, Task):
                if task.procId is not None:
                    continue
                est, eft, pid = find_processor(task, schedule)
                latest_start = est  # AST

                if format == 'default':
                    # allocate input tensor
                    if task is entry_task:
                        self.memory.fit(
                            input, [est, eft], task, can_delay=False)
                    # allocate output tensor
                    self.memory.fit(task.output, [
                        est, eft if task.is_exit() else Memory.DEADLINE], task, final=False, can_delay=False)

                    self.memory.fit(
                        task.buffer_size, [latest_start, latest_start + eft - est], task, can_delay=False)
                else:
                    # allocate memory
                    for m_edge in task.m_in_edges:
                        if m_edge.source.type == 'allocate':
                            ok, _ = self.memory.fit(m_edge.source.buffer, [
                                est, eft if task.id == task_count else Memory.DEADLINE], m_edge.source, final=False)
                            if not ok:
                                raise ValueError('Fail to allocate memory')

                ast = latest_start
                aft = latest_start + eft - est

                task.procId = pid + 1
                task.ast = ast
                task.aft = aft
                schedule[pid].append(task)

                if format == 'default':
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
                else:
                    # free tensors
                    for m_edge in task.m_out_edges:
                        if m_edge.target.type == 'free':
                            last_use = True
                            until = -1
                            for in_edge in m_edge.target.t_in_edges:
                                if in_edge.source.procId is None:
                                    last_use = False
                                    break
                                until = max(until, in_edge.source.aft)
                            if last_use:
                                until = max(until, aft)
                                self.memory.free_tensor(m_edge.target, until)

                if task.aft > makespan:
                    makespan = task.aft

            # update heap
            for out_edge in task.out_edges:
                last_use = True
                for in_edge in out_edge.target.t_in_edges:
                    if in_edge.source.procId is None:
                        last_use = False
                if last_use:
                    heappush(task_heap, out_edge.target)

        if options.get('plot', True):
            suffix = options.get('suffix', '')
            self.memory.plot(
                makespan, filename=f'heft-base{suffix}')
            self.plot(schedule, makespan, f'heft-base{suffix}')
        return schedule, makespan, self.memory.max()

    def print_priority(self, entry_node: Task):
        print('''UPPER RANKS
---------------------------
Task    Rank
---------------------------''')
        self.bfs(entry_node, op=lambda task: print(
            f'{task.id}       {round(task.priority, 4)}'))


def task_compare(task1: Task, task2: Task):
    # return task2.priority - task1.priority
    if task2.priority == task1.priority:
        return task2.id - task1.id
    else:
        return task2.priority - task1.priority


def calculate_priority(task: Union[Task, MTask]):
    if task.priority:
        return task.priority
    max = 0
    for edge in task.out_edges:
        cost = (edge.weight if hasattr(
            edge, 'weight') else 0) + calculate_priority(edge.target)
        if cost > max:
            max = cost
    task.priority = (task.cost_avg if hasattr(task, 'cost_avg') else 0) + max
    return task.priority


def find_processor(task: Task, schedule):
    min_eft_procId = np.argmin(task.cost_table)
    is_entry = len(task.t_in_edges) == 0
    min_eft = sys.maxsize
    # Calculate start time
    selected_ast = est = 0 if is_entry else max(
        [edge.source.aft if edge.source.aft else 0 for edge in task.t_in_edges])
    # # Choose a processor
    for pid, cost in enumerate(task.cost_table):
        proc_est = schedule[pid][-1].aft if len(
            schedule[pid]) > 0 else est

        # Check if current task and its parents are on the same processor
        undones = []
        for in_edge in task.t_in_edges:
            # parent not scheduled yet, cannot schedule this task
            if not in_edge.source.procId:
                if in_edge.source.id != 0:
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
