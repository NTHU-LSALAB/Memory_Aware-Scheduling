from functools import reduce
from heapq import heapify, heappop, heappush

import numpy as np
from algorithms.algo_base import AlgoBase
from algorithms.cpop import calculate_priority, find_processor
from lib.utils import ssse

from platforms.memory import Memory
from platforms.task import Task


def adjust_priority(tasks: list[Task]):
    for task in tasks:
        if len(task.m_out_edges) > 0 and task.id != 0:  # releaser
            releaser = task
            release_mIds = list(
                map(lambda edge: edge.target.mId, task.m_out_edges))
            releaser_pairs = []
            for p_task in tasks:
                # pair need to be consumer
                for edge in p_task.m_in_edges:
                    if edge.source.mId in release_mIds:
                        releaser_pairs.append(p_task)

            vc_list = []
            for adj_edge in releaser.t_in_edges:  # adj
                if len(adj_edge.source.m_in_edges) > 0:  # consumer
                    consumer = adj_edge.source
                    consume_mIds = list(
                        map(lambda edge: edge.source.mId, consumer.m_in_edges))
                    consumer_pairs = []
                    for p_task in tasks:
                        # pair need to be releaser
                        for edge in p_task.m_out_edges:
                            if edge.target.mId in consume_mIds:
                                consumer_pairs.append(p_task)
                    if consumer.priority < np.average(list(map(lambda pair: pair.priority, releaser_pairs))):
                        vc_list.append(consumer)
                        continue
                    isnot_adj = True
                    for c_pair in consumer_pairs:
                        for r_pair in releaser_pairs:
                            if r_pair in list(map(lambda edge: edge.target, c_pair.t_out_edges)):
                                isnot_adj = False
                    if isnot_adj:
                        vc_list.append(consumer)
            for adj_edge in releaser.t_out_edges:  # adj
                if len(adj_edge.target.m_in_edges) > 0:  # consumer
                    consumer = adj_edge.source
                    consume_mIds = list(
                        map(lambda edge: edge.source.mId, consumer.m_in_edges))
                    consumer_pairs = []
                    for p_task in tasks:
                        # pair need to be releaser
                        for edge in p_task.m_out_edges:
                            if edge.target.mId in consume_mIds:
                                consumer_pairs.append(p_task)
                    if consumer.priority < np.average(list(map(lambda pair: pair.priority, releaser_pairs))):
                        vc_list.append(consumer)
                        continue
                    isnot_adj = True
                    for c_pair in consumer_pairs:
                        for r_pair in releaser_pairs:
                            if r_pair in list(map(lambda edge: edge.target, c_pair.t_out_edges)):
                                isnot_adj = False
                    if isnot_adj:
                        vc_list.append(consumer)
            releaser.priority += reduce(lambda prev,
                                        curr: prev + curr.priority, vc_list, 0)


def sbac_find_processor(task, schedule):
    return find_processor(task, schedule)


class CPOPSBAC(AlgoBase):

    def schedule(self, tasks: list[Task], input, options={}, format='default') -> tuple[list[list[Task]], int]:
        # print('SBAC')
        makespan = 0
        entry_task, _ = ssse(tasks)

        calculate_priority(entry_task)
        adjust_priority(tasks)

        schedule: list[list[Task]] = [[]
                                      for _ in range(len(entry_task.cost_table))]

        task_heap = [entry_task]
        heapify(task_heap)

        while len(task_heap):
            task = heappop(task_heap)

            if isinstance(task, Task):
                if task.procId is not None:
                    continue
                est, eft, pid = sbac_find_processor(task, schedule)
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
                                est,  Memory.DEADLINE], m_edge.source, final=False)
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
                makespan, filename=f'cpop-sbac{suffix}')
            self.plot(schedule, makespan, f'cpop-sbac{suffix}')
        return schedule, makespan, self.memory.max()

    def print_priority(self, entry_node: Task):
        print('''UPPER RANKS
---------------------------
Task    Rank
---------------------------''')
        self.bfs(entry_node, op=lambda task: print(
            f'{task.id}       {round(task.priority, 4)}'))
