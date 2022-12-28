from copy import deepcopy
from functools import cmp_to_key
from heapq import heapify, heappop, heappush
from algorithms.algo_base import AlgoBase
from algorithms.heft import calculate_priority, find_processor
from lib.utils import ssse
from platforms.memory import Memory
from platforms.task import Task


class HEFTLookup(AlgoBase):

    def schedule(self, tasks: list[Task], input, options: dict, format='default') -> tuple[list[list[Task]], int]:
        self.format = format
        # print('lookup version')
        self.options = options
        self.input = input
        self.reserved_list = []
        self.makespan = 0

        self.task_count = len(list(filter(lambda task: isinstance(task, Task), tasks)))
        entry_task, _ = ssse(tasks)

        # calculate priority
        calculate_priority(entry_task)

        self.schedule: list[list[Task]] = [[]
                                           for _ in range(len(entry_task.cost_table))]

        self.task_heap = [entry_task]
        heapify(self.task_heap)

        # for rollback
        while len(self.task_heap):
            task = heappop(self.task_heap)
            self.rollback_list = []
            if isinstance(task, Task) and task not in self.reserved_list:
                # print('============', task.id, '==============')
                success = self.reserve(task, options.get('depth', 1))
                # print('success:', success)
                # print(list(map(lambda task: task.id, self.reserved_list)))
                if not success:
                    self.rollback(task)

            # update heap
            for out_edge in task.out_edges:
                if out_edge.target not in self.task_heap:
                    heappush(self.task_heap, out_edge.target)
        if len(list(filter(lambda task: isinstance(task, Task)
                           and task.procId == None, tasks))):
            raise ValueError('Fail to allocate memory')
        if options.get('plot', True):
            suffix = options.get('suffix', '')
            self.memory.plot(
                self.makespan, filename=f'heft-lookup{suffix}')
            if options.get('snapshot'):
                self.memory.plot_snapshot(
                    self.makespan, filename=f'heft-lookup{suffix}')
            self.plot(self.schedule, self.makespan, f'heft-lookup{suffix}')
        return self.schedule, self.makespan, self.memory.max()

    def reserve(self, task: Task, depth=1):
        return self.__reserve_re(task, depth)
        # tasks = self.__collect_tasks(task, depth)
        # can_reserve = True
        # for t in sorted(tasks):
        #     can_reserve = can_reserve and self.allocate_dependencies(t)

        # return can_reserve

    def __collect_tasks(self, task: Task, depth=1):
        if depth == -1:
            return []

        tasks = [task]
        # can_reserve = self.allocate_dependencies(task)

        # reserve for children
        for edge in task.t_out_edges:
            tasks.extend(self.__collect_tasks(
                edge.target, depth-1))

        return tasks

    def __reserve_re(self, task: Task, depth):
        if depth == -1:
            return True

        can_reserve = self.allocate_dependencies(task)

        # reserve for children
        for edge in task.t_out_edges:
            can_reserve = can_reserve and self.__reserve_re(
                edge.target, depth-1)

        return can_reserve

    def allocate_memory(self, task: Task):
        # Already allocated
        if task in self.reserved_list:
            return True
        # For rollback
        if task not in self.rollback_list:
            self.rollback_list.append(task)

        ####################### Schedule the task on a proccessor #######################
        est, eft, pid = find_processor(task, self.schedule)
        ################################ Allocate memory ################################
        checked = True  # Accumulate checked
        latest_start = est  # AST
        # Allocate input tensor
        if self.format == 'default':
            if task.is_entry():
                ok, slot = self.memory.fit(
                    self.input, [est, eft], task)
                if slot:
                    latest_start = max(latest_start, slot.interval[0])
                checked = checked and ok

            # Allocate a task's output tensor
            ok, slot = self.memory.fit(task.output, [
                est, eft if task.is_exit() else Memory.DEADLINE], task, final=False)
            if slot:
                latest_start = max(latest_start, slot.interval[0])
            checked = checked and ok

            # Allocate internal buffer
            ok, slot = self.memory.fit(
                task.buffer_size, [latest_start, latest_start + eft - est], task)
            if slot:
                latest_start = max(latest_start, slot.interval[0])
            checked = checked and ok
        else:
            # allocate memory
            for m_edge in task.m_in_edges:
                if m_edge.source.type == 'allocate':
                    ok, slot = self.memory.fit(m_edge.source.buffer, [
                        est, eft if task.id == self.task_count else Memory.DEADLINE], m_edge.source, final=False)
                    if slot:
                        latest_start = max(
                            latest_start, slot.interval[0])
                    checked = checked and ok

        # Now we know the ast, aft
        ast = latest_start
        aft = latest_start + eft - est

        if checked:

            self.reserved_list.append(task)
            task.procId = pid + 1
            task.ast = ast
            task.aft = aft

            if self.format == 'default':
                # Free input tensors
                if not task.is_entry():
                    # check if inputs can be free
                    for in_edge in task.t_in_edges:
                        # if task.id == 15:
                        #     print('parent:', in_edge.source.id)
                        last_use = True
                        until = -1
                        # if task.id == 15:
                        #     print('siblings:')
                        for out_edge in in_edge.source.t_out_edges:
                            # if task.id == 15:
                            #     print(out_edge.target.id)
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

            self.schedule[pid].append(task)
            # update makespan
            if task.aft > self.makespan:
                self.makespan = task.aft
        return checked

    def rollback(self, task, depth=1):
        if depth == -1:
            return True

        # print('Rollback:', list(map(lambda task: task.id, self.rollback_list)))
        for t in self.rollback_list:
            # reset task value
            t.rollback()
            # remove from reserve list
            if t in self.reserved_list:
                self.reserved_list.remove(t)
            if self.format == 'default':
                # remove memory allocation
                self.memory.rollback(t.id)
            else:
                for m_edge in t.m_in_edges:
                    self.memory.rollback(m_edge.source.id)
            # remove from memory
            for proc_schedule in self.schedule:
                for slot in proc_schedule:
                    if t.id == slot.id:
                        proc_schedule.remove(t)
            # remove successors from ready q
            # for out_edge in task.out_edges:
            #     if out_edge.target in self.task_heap:
            #         self.task_heap.remove(out_edge.target)

    def allocate_dependencies(self, task: Task):
        checked = True
        def edge_compare(edge1, edge2):
            task1 = edge1.source
            task2 = edge2.source
            if task1.priority == task2.priority:
                return task1.id > task2.id
            else:
                return task1.priority > task2.priority
        # print('current:', task.id)
        for edge in sorted(task.t_in_edges, key=cmp_to_key(edge_compare)):
            # print(edge.source.priority)
            checked = checked and self.allocate_dependencies(edge.source)
        return checked and self.allocate_memory(task)

    def print_priority(self, entry_task: Task):
        print('''UPPER RANKS
---------------------------
Task    Rank
---------------------------''')
        self.bfs(entry_task, op=lambda task: print(
            f'{task.id}       {round(task.priority, 4)}'))
