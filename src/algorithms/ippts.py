from heapq import heapify, heappop, heappush
import sys
from algorithms.algo_base import AlgoBase
from functools import cmp_to_key
import numpy as np

from platforms.memory import Memory
from platforms.task import Task


class IPPTS(AlgoBase):

    def schedule(self, tasks: list[Task], input, options={}, format='default') -> tuple[list[list[Task]], int]:
        # print('HEFT')
        self.memory = Memory(sys.maxsize)
        makespan = 0
        entry_task = next(
            (task for task in tasks if len(task.in_edges) == 0), None)
        exit_task = next(
            (task for task in tasks if len(task.out_edges) == 0), None)

        if entry_task is None or exit_task is None:
            raise ValueError('No entry or exit node')

        calculate_pcm(entry_task)
        for task in tasks:
            calculate_priority(task)

        schedule: list[list[Task]] = [[]
                                      for _ in range(len(entry_task.cost_table))]
        task_heap = [entry_task]
        heapify(task_heap)
        while len(task_heap):
            task = heappop(task_heap)

            ast, aft, pid = find_processor(task, schedule)
            # print(ast, aft, pid)

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
            # update heap
            for out_edge in task.out_edges:
                last_use = True
                for in_edge in out_edge.target.in_edges:
                    if in_edge.source.procId is None:
                        last_use = False
                if last_use:
                    heappush(task_heap, out_edge.target)
                    
            if task.aft > makespan:
                makespan = task.aft

        self.plot(schedule, makespan, 'ippts-base')
        return schedule, makespan, self.memory.max()


def task_compare(task1: Task, task2: Task):
    return task2.priority - task1.priority


def calculate_priority(task: Task):

    if task.priority:
        return task.priority
    # max = 0
    # for edge in task.out_edges:
    #     cost = edge.weight + calculate_priority(edge.target)
    #     if cost > max:
    #         max = cost
    # task.priority = task.cost_avg + max
    rank_pcm = np.average(task.pcm)
    p_rank = rank_pcm * len(task.out_edges)
    task.priority = p_rank
    return task.priority


def calculate_pcm(task: Task):

    if task.pcm[0]:
        return task.pcm

    for i in range(len(task.cost_table)):
        max = task.cost_table[i]
        for edge in task.out_edges:
            min = sys.maxsize
            for cid, cost in enumerate(edge.target.cost_table):
                pcm = calculate_pcm(edge.target)
                tmp = pcm[cid] + task.cost_table[cid] + \
                    cost + (edge.weight if i != cid else 0)
                if tmp < min:
                    min = tmp
            if min > max:
                max = min
        task.pcm[i] = max
    return task.pcm


def find_processor(task: Task, schedule):
    min_eft_procId = np.argmin(task.cost_table)
    min_eft = task.cost_table[min_eft_procId] if task.is_entry(
    ) else sys.maxsize
    min_lhead_eft = sys.maxsize
    # Calculate start time
    selected_ast = est = 0 if task.is_entry() else max(
        [edge.source.aft if edge.source.aft else 0 for edge in task.in_edges])
    # Choose a processor
    for pid, cost in enumerate(task.cost_table):
        proc_est = schedule[pid][-1].aft if len(
            schedule[pid]) > 0 else est
        lhet = task.pcm[pid] - cost

        # Check if current task and its parents are on the same processor
        for in_edge in task.in_edges:
            if in_edge.source.procId-1 != pid:
                proc_est = max(in_edge.source.aft +
                               in_edge.weight, proc_est)
        eft = proc_est + cost
        lhead_eft = eft + lhet
        if lhead_eft < min_lhead_eft:
            selected_ast = proc_est
            min_eft_procId = pid
            min_eft = eft
            min_lhead_eft = lhead_eft

    return selected_ast, min_eft, min_eft_procId
