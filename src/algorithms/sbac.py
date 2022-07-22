from heapq import heapify, heappop, heappush
from importlib.metadata import entry_points
import sys

import numpy as np
from algorithms.algo_base import AlgoBase
from algorithms.heft import calculate_priority
from platforms.dep import Dep
from platforms.task import MTask
from platforms.memory import Memory
from platforms.task import Task


def adjust_priority(entry_task):
    pass


def abac_find_processor(task: Task, schedule):
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


class SBAC(AlgoBase):

    def schedule(self, tasks: list[Task], input, options: dict, format='default') -> tuple[list[list[Task]], int]:
        # print('delay version')
        makespan = 0
        entry_tasks = list(filter(lambda task: task.is_entry(), tasks))
        exit_tasks = list(filter(lambda task: task.is_exit(), tasks))

        if len(entry_tasks) == 0 or len(exit_tasks) == 0:
            raise ValueError('No entry or exit nodes')

        if len(entry_tasks) > 1:
            entry_task = Task(0, [0, 0, 0], 0, 0)
            tasks.insert(0, entry_task)
            for task in entry_tasks:
                edge = Dep(entry_task, task, 0, 0)
                entry_task.out_edges.append(edge)
                task.in_edges.append(edge)
        else:
            entry_task = entry_tasks[0]

        if len(exit_tasks) > 1:
            exit_task = Task(len(tasks), [0, 0, 0], 0, 0)
            tasks.append(exit_task)
            for task in exit_tasks:
                edge = Dep(task, exit_task, 0, 0)
                task.out_edges.append(edge)
                exit_task.in_edges.append(edge)
        else:
            exit_task = exit_tasks[0]

        calculate_priority(entry_task)

        schedule: list[list[Task]] = [[]
                                      for _ in range(len(entry_task.cost_table))]
        task_heap = entry_tasks
        heapify(task_heap)

        while len(task_heap):
            task = heappop(task_heap)

            if isinstance(task, Task):
                if task.procId is not None:
                    continue
                # print(task.id)
                est, eft, pid = abac_find_processor(task, schedule)
                latest_start = est  # AST

                # allocate memory
                for m_edge in task.m_in_edges:
                    if m_edge.source.type == 'allocate':
                        ok, slot = self.memory.fit(m_edge.source.buffer, [
                            est,  Memory.DEADLINE], m_edge.source, final=False)
                        if not ok:
                            raise ValueError('Fail to allocate memory')
                        if slot:
                            latest_start = max(latest_start, slot.interval[0])

                ast = latest_start
                aft = latest_start + eft - est

                # append task to schedule
                task.procId = pid + 1
                task.ast = ast
                task.aft = aft
                schedule[pid].append(task)

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

                # update makespan
                if task.aft > makespan:
                    makespan = task.aft

            # update heap
            for out_edge in task.t_out_edges:
                last_use = True
                for in_edge in out_edge.target.t_in_edges:
                    if in_edge.source.procId is None:
                        last_use = False
                if last_use:
                    heappush(task_heap, out_edge.target)

        if options.get('plot', True):
            suffix = options.get('suffix', '')
            self.memory.plot(
                makespan, filename=f'sbac{suffix}')
            self.plot(schedule, makespan, f'sbac{suffix}')
        return schedule, makespan, self.memory.max()
