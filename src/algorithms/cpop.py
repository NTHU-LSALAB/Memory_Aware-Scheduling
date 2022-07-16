from heapq import heapify, heappop, heappush
import sys
from algorithms.algo_base import AlgoBase
from functools import cmp_to_key
import numpy as np

from platforms.memory import Memory
from platforms.task import Task


class CPOP(AlgoBase):

    def schedule(self, tasks: list[Task], input, options={}) -> tuple[list[list[Task]], int]:
        # print('CPOP')
        self.memory = Memory(sys.maxsize)
        makespan = 0
        entry_task = next(
            (task for task in tasks if len(task.in_edges) == 0), None)
        exit_task = next(
            (task for task in tasks if len(task.out_edges) == 0), None)

        if entry_task is None or exit_task is None:
            raise ValueError('No entry or exit node')

        calculate_priority(entry_task, exit_task)
        for task in tasks:
            task.priority = task.rank_upward + task.rank_downward
        set_critical_node(entry_task)
        critical_procId = find_critical_processor(entry_task)

        schedule: list[list[Task]] = [[]
                                      for _ in range(len(entry_task.cost_table))]

        task_heap = [entry_task]
        heapify(task_heap)

        while len(task_heap):
            task = heappop(task_heap)
            ast, aft, pid = find_processor(task, schedule, critical_procId)

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

        self.plot(schedule, makespan, 'cpop-base')
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


def set_critical_node(task: Task):
    task.is_critical = True

    critical_id = 0
    max_priority = 0
    for i, out_edge in enumerate(task.out_edges):
        if out_edge.target.priority > max_priority:
            max_priority = out_edge.target.priority
            critical_id = i
    if task.out_edges:
        set_critical_node(task.out_edges[critical_id].target)


def find_critical_processor(task: Task):
    cost = culumlative_cost(task)
    return np.argmin(cost)


def culumlative_cost(task: Task):
    cost = task.cost_table
    for out_edge in task.out_edges:
        if out_edge.target.is_critical:
            cost = [sum(x)
                    for x in zip(cost, culumlative_cost(out_edge.target))]
            break
    return cost


def calculate_priority(entry_task: Task, exit_task: Task):
    calculate_rank_downward(exit_task)
    calculate_rank_upward(entry_task)


def calculate_rank_upward(task: Task):
    if task.rank_upward:
        return task.rank_upward
    max = 0
    for edge in task.out_edges:
        cost = edge.weight + calculate_rank_upward(edge.target)
        if cost > max:
            max = cost
    task.rank_upward = task.cost_avg + max
    return task.rank_upward


def calculate_rank_downward(task: Task):
    if task.rank_downward:
        return task.rank_downward
    max = 0
    for edge in task.in_edges:
        cost = edge.weight + edge.source.cost_avg + \
            calculate_rank_downward(edge.source)
        if cost > max:
            max = cost
    task.rank_downward = max
    return task.rank_downward


def find_processor(task: Task, schedule, critical_procId):
    if task.is_critical:
        min_eft_procId = critical_procId
        min_eft = task.cost_table[min_eft_procId] if task.is_entry(
        ) else sys.maxsize
        cost = task.cost_table[min_eft_procId]
        # Calculate start time
        selected_ast = est = 0 if task.is_entry() else max(
            [edge.source.aft if edge.source.aft else 0 for edge in task.in_edges])
        proc_est = schedule[critical_procId][-1].aft if len(
            schedule[critical_procId]) > 0 else est
        # Check if current task and its parents are on the same processor
        undones = []
        for in_edge in task.in_edges:
            # parent not scheduled yet, cannot schedule this task
            if not in_edge.source.procId:
                undones.append(in_edge.source)
                continue
            if in_edge.source.procId-1 != critical_procId:
                proc_est = max(in_edge.source.aft +
                               in_edge.weight, proc_est)
        if undones:
            raise Exception(undones)
        eft = proc_est + cost
        if eft < min_eft:
            selected_ast = proc_est
            min_eft = eft
    else:
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
