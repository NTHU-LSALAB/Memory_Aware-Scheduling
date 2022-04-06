from sys import maxsize
from algorithms.algo_base import AlgoBase
from graph.node import Node
from functools import cmp_to_key
import numpy as np
from platforms.memory import Memory


def task_compare(task1: Node, task2: Node):
    return task2.rank - task1.rank


class HEFTLookup(AlgoBase):

    def schedule(self, tasks: list[Node], input) -> tuple[list[list[Node]], int]:
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
        self.schedule: list[list[Node]] = [[]
                                           for _ in range(len(self.entry_task.cost_table))]
        sorted_tasks = sorted_tasks
        # for rollback
        self.round = 1
        for task in sorted_tasks:
            print('===================Task', task.id, 'start===================')
            self.reserve(task)
            self.round = self.round + 1

        self.memory.plot(self.makespan, filename='mem-heft-lookup')
        self.plot(self.schedule, self.makespan, 'heft-lookup')
        return self.schedule, self.makespan

    def reserve(self, task: Node, depth=1, root=True):
        if depth == -1:
            return True

        print('reserve ', task.id)
        can_reserve = True

        can_reserve = can_reserve and self.allocate_dependencies(task)

        # reserve for children
        for edge in task.out_edges:
            can_reserve = can_reserve and self.reserve(
                edge.target, depth-1, root=False)

        if not can_reserve and root:
            self.rollback(task)

        return can_reserve

    def allocate_memory(self, task: Node, check=False):
        if task in self.reserved_list:
            return True
        print('allocate', task.id)
        min_eft_procId = np.argmin(task.cost_table)
        min_eft = task.cost_table[min_eft_procId] if task is self.entry_task else maxsize
        # calculate start time
        selected_ast = est = 0 if task is self.entry_task else max(
            [edge.source.aft for edge in task.in_edges])
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
        checked = True
        if task is self.entry_task:
            checked = checked and self.memory.first_fit(
                self.input, [selected_ast, min_eft], task)

        # allocate output tensor
        if task is self.exit_task:
            checked = checked and self.memory.first_fit(
                task.output, [selected_ast, min_eft], task)
        else:
            # allocate task's output tensor
            checked = checked and self.memory.first_fit(task.out_edges[0].size, [
                selected_ast, Memory.DEADLINE], task, final=False)

        # allocate internal buffer
        checked = checked and self.memory.first_fit(
            task.buffer_size, [selected_ast, min_eft], task, check=check)

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
                    until = max(until, min_eft)
                    self.memory.free_tensor(in_edge.source, until)

        task.procId = min_eft_procId + 1
        task.ast = selected_ast
        task.aft = min_eft
        task.round = self.round
        self.schedule[min_eft_procId].append(task)
        # update makespan
        if task.aft > self.makespan:
            self.makespan = task.aft

        if checked:
            task.round = self.round
            self.reserved_list.append(task)
        return checked

    def rollback(self, task, depth = 1):
        if depth == -1:
            return True

        print('rollback', task.id)
        
        # rollback for children
        for edge in task.out_edges:
            self.rollback(edge.target, depth-1)
        
        if task in self.reserved_list and task.round == self.round:
            self.reserved_list.remove(task)
        self.memory.rollback(task.id, self.round)
        for proc_schedule in self.schedule:
            for t in proc_schedule:
                if t.id == task.id:
                    print(t.id, t.round, task.round)
                    if t.round == task.round:
                        proc_schedule.remove(t)

    def allocate_dependencies(self, task: Node):
        checked = True
        for edge in task.in_edges:
            checked = checked and self.allocate_dependencies(edge.source)
        return checked & (self.allocate_memory(task, check=True) or task in self.reserved_list)

    def calculate_rank(self, task: Node):
        if task.rank:
            return task.rank
        max = 0
        for edge in task.out_edges:
            cost = edge.weight + self.calculate_rank(edge.target)
            if cost > max:
                max = cost
        task.rank = task.cost_avg + max
        return task.rank

    def print_rank(self, entry_task: Node):
        print('''UPPER RANKS
---------------------------
Task    Rank
---------------------------''')
        self.bfs(entry_task, op=lambda task: print(
            f'{task.id}       {round(task.rank, 4)}'))
