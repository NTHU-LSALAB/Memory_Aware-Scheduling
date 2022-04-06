from sys import maxsize
from algorithms.algo_base import AlgoBase
from functools import cmp_to_key
import numpy as np
from platforms.memory import Memory
from platforms.task import Task


def task_compare(task1: Task, task2: Task):
    return task2.rank - task1.rank


class HEFTLookup(AlgoBase):

    def schedule(self, tasks: list[Task], input) -> tuple[list[list[Task]], int]:
        print('lookup version')
        self.input = input
        self.reserved_list = []
        self.makespan = 0
        self.entry_task = next(
            (task for task in tasks if len(task.in_edges) == 0), None)
        self.exit_task = next(
            (task for task in tasks if len(task.out_edges) == 0), None)

        if self.entry_task is None or self.exit_task is None:
            raise ValueError('No entry or exit node')

        self.calculate_rank(self.entry_task)
        sorted_tasks = sorted(tasks, key=cmp_to_key(task_compare))
        self.schedule: list[list[Task]] = [[]
                                           for _ in range(len(self.entry_task.cost_table))]
        sorted_tasks = sorted_tasks

        # for rollback
        for task in sorted_tasks:
            print('========================')
            print('Reserve', task.id)
            print('========================')
            self.round_list = []
            success = self.reserve(task)
            print('success:', success)
            if not success:
                self.rollback(task)
            print('Reserved_list:', list(
                map(lambda task: task.id, self.reserved_list)))

        self.memory.plot(self.makespan, filename='mem-heft-lookup')
        self.plot(self.schedule, self.makespan, 'heft-lookup')
        return self.schedule, self.makespan

    def reserve(self, task: Task, depth=1):
        return self.__reserve_re(task, depth)

    def __reserve_re(self, task: Task, depth):
        if depth == -1:
            return True

        if task not in self.round_list:
            self.round_list.append(task)
        can_reserve = self.allocate_dependencies(task)

        # reserve for children
        for edge in task.out_edges:
            can_reserve = can_reserve and self.__reserve_re(
                edge.target, depth-1)

        return can_reserve

    def allocate_memory(self, task: Task):
        # already allocated
        if task in self.reserved_list:
            return True
        print('Allocate', task.id)
        min_eft_procId = np.argmin(task.cost_table)
        min_eft = task.cost_table[min_eft_procId] if task is self.entry_task else maxsize
        # calculate start time
        selected_ast = est = 0 if task is self.entry_task else max(
            [edge.source.aft if edge.source.aft else 0 for edge in task.in_edges])
        # choose a processor
        for pid, cost in enumerate(task.cost_table):
            proc_est = self.schedule[pid][-1].aft if len(
                self.schedule[pid]) > 0 else est

            # check if current task and its parents are on the same processor
            for in_edge in task.in_edges:
                if in_edge.source.procId-1 != pid:
                    proc_est = max(in_edge.source.aft +
                                   in_edge.weight, proc_est)
            eft = proc_est + cost
            if eft < min_eft:
                selected_ast = proc_est
                min_eft = eft
                min_eft_procId = pid
        # Check memory
        checked = True
        latest_start = selected_ast
        if task is self.entry_task:
            ok, slot = self.memory.first_fit(
                self.input, [selected_ast, min_eft], task)
            if slot:
                latest_start = max(latest_start, slot.interval[0])
            checked = checked and ok

        # allocate output tensor
        if task is self.exit_task:
            ok, slot = self.memory.first_fit(
                task.output, [selected_ast, min_eft], task)
            if slot:
                latest_start = max(latest_start, slot.interval[0])
            checked = checked and ok
        else:
            # allocate task's output tensor
            ok, slot = self.memory.first_fit(task.out_edges[0].size, [
                selected_ast, Memory.DEADLINE], task, final=False)
            if slot:
                latest_start = max(latest_start, slot.interval[0])
            checked = checked and ok

        # allocate internal buffer
        ok, slot = self.memory.first_fit(
            task.buffer_size, [latest_start, latest_start + min_eft - selected_ast], task, est=latest_start)
        if slot:
            latest_start = max(latest_start, slot.interval[0])
        checked = checked and ok

        if checked:
            # free input tensors
            if task is not self.entry_task:
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
                        until = max(until, latest_start +
                                    (min_eft - selected_ast))
                        self.memory.free_tensor(in_edge.source, until)
            self.reserved_list.append(task)
            task.procId = min_eft_procId + 1
            task.ast = latest_start
            task.aft = latest_start + (min_eft - selected_ast)
            self.schedule[min_eft_procId].append(task)
            # update makespan
            if task.aft > self.makespan:
                self.makespan = task.aft
        return checked

    def rollback(self, task, depth=1):
        if depth == -1:
            return True

        print('Rollback:', list(map(lambda task: task.id, self.round_list)))
        for task in self.round_list:
            task.rollback()
            if task in self.reserved_list:
                self.reserved_list.remove(task)
            self.memory.rollback(task.id)
            for proc_schedule in self.schedule:
                for t in proc_schedule:
                    if t.id == task.id:
                        proc_schedule.remove(t)

        # if task in self.reserved_list and task.round == self.round:
        #     self.reserved_list.remove(task)
        # self.memory.rollback(task.id, self.round)
        # for proc_schedule in self.schedule:
        #     for t in proc_schedule:
        #         if t.id == task.id and t.round == task.round:
        #             proc_schedule.remove(t)

    def allocate_dependencies(self, task: Task):
        if task not in self.round_list:
            self.round_list.append(task)
        checked = True
        for edge in task.in_edges:
            checked = checked and self.allocate_dependencies(edge.source)
        return checked and self.allocate_memory(task)

    def calculate_rank(self, task: Task):
        if task.rank:
            return task.rank
        max = 0
        for edge in task.out_edges:
            cost = edge.weight + self.calculate_rank(edge.target)
            if cost > max:
                max = cost
        task.rank = task.cost_avg + max
        return task.rank

    def print_rank(self, entry_task: Task):
        print('''UPPER RANKS
---------------------------
Task    Rank
---------------------------''')
        self.bfs(entry_task, op=lambda task: print(
            f'{task.id}       {round(task.rank, 4)}'))
