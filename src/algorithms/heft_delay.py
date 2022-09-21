from heapq import heapify, heappop, heappush
from algorithms.algo_base import AlgoBase
from algorithms.heft import calculate_priority, find_processor
from lib.utils import ssse

from platforms.memory import Memory
from platforms.task import Task


class HEFTDelay(AlgoBase):

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
                # print('==============',task.id, '=============')
                est, eft, pid = find_processor(task, schedule)
                latest_start = est  # AST

                if format == 'default':
                    # allocate input tensor
                    if task is entry_task:
                        _, slot = self.memory.fit(
                            input, [est, eft], task)
                        if slot:
                            latest_start = max(latest_start, slot.interval[0])
                    # allocate output tensor
                    ok, slot = self.memory.fit(task.output, [
                        est, eft if task.is_exit() else Memory.DEADLINE], task, final=False)
                    if not ok:
                        raise ValueError('Fail to allocate memory')
                    if slot:
                        latest_start = max(latest_start, slot.interval[0])

                    ok, slot = self.memory.fit(
                        task.buffer_size, [latest_start, latest_start + eft - est], task)
                    if not ok:
                        raise ValueError('Fail to allocate memory')
                    if slot:
                        latest_start = max(latest_start, slot.interval[0])
                else:
                    # allocate memory
                    for m_edge in task.m_in_edges:
                        if m_edge.source.type == 'allocate':
                            ok, slot = self.memory.fit(m_edge.source.buffer, [
                                est, eft if task.id == task_count else Memory.DEADLINE], m_edge.source, final=False)
                            if not ok:
                                raise ValueError('Fail to allocate memory')
                            if slot:
                                latest_start = max(
                                    latest_start, slot.interval[0])

                ast = latest_start
                aft = latest_start + eft - est

                task.procId = pid + 1
                task.ast = ast
                task.aft = aft
                schedule[pid].append(task)

                if format == 'default' and task.id != 0:
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
                elif task.id != 0:
                    # free tensors
                    # print(f'======== {task.id} ========')
                    for m_edge in task.m_out_edges:
                        if m_edge.target.type == 'free':
                            last_use = True
                            until = -1
                            # print(m_edge.target.id)
                            for in_edge in m_edge.target.t_in_edges:
                                if in_edge.source.procId is None:
                                    last_use = False
                                    break
                                until = max(until, in_edge.source.aft)
                            if last_use:
                                # print(task.id, 'free', 'mId:', m_edge.target.mId)
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
                makespan, filename=f'heft-delay{suffix}')
            self.plot(schedule, makespan, f'heft-delay{suffix}')
        return schedule, makespan, self.memory.max()

    def print_priority(self, entry_node: Task):
        print('''UPPER RANKS
---------------------------
Task    Rank
---------------------------''')
        self.bfs(entry_node, op=lambda task: print(
            f'{task.id}       {round(task.priority, 4)}'))
