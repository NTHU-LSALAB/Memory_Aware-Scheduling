import sys
from algorithms.algo_base import AlgoBase
import numpy as np
from decorators import base, delay, reserve, sbac

from platforms.task import Task

@base('cpop')
class CPOP(AlgoBase):
    def task_compare(self, task1: Task, task2: Task):
        if task2.priority == task1.priority:
            return task2.id - task1.id
        else:
            return task2.priority - task1.priority


    def set_critical_node(self, task: Task):
        task.is_critical = True

        critical_id = 0
        max_priority = 0
        for i, out_edge in enumerate(task.out_edges):
            if out_edge.target.priority > max_priority:
                max_priority = out_edge.target.priority
                critical_id = i
        if task.out_edges:
            self.set_critical_node(task.out_edges[critical_id].target)


    def find_critical_processor(self, task: Task):
        cost = self.culumlative_cost(task)
        return np.argmin(cost)


    def culumlative_cost(self, task: Task):
        cost = task.cost_table
        for out_edge in task.t_out_edges:
            if out_edge.target.is_critical:
                cost = [sum(x)
                        for x in zip(cost, self.culumlative_cost(out_edge.target))]
                break
        return cost


    def calculate_priority(self, entry_task: Task, exit_task: Task):
        self.calculate_rank_downward(exit_task)
        self.calculate_rank_upward(entry_task)
        for task in self.tasks:
            task.priority = task.rank_upward + task.rank_downward
        self.set_critical_node(entry_task)
        self.critical_procId = self.find_critical_processor(entry_task)


    def calculate_rank_upward(self, task: Task):
        if task.rank_upward:
            return task.rank_upward
        max = 0
        for edge in task.out_edges:
            cost = (edge.weight if hasattr(
                edge, 'weight') else 0) + self.calculate_rank_upward(edge.target)
            if cost > max:
                max = cost
        task.rank_upward = (task.cost_avg if hasattr(
            task, 'cost_avg') else 0) + max
        return task.rank_upward


    def calculate_rank_downward(self, task: Task):
        if task.rank_downward:
            return task.rank_downward
        max = 0
        for edge in task.in_edges:
            cost = (edge.weight if hasattr(
                edge, 'weight') else 0) + (edge.source.cost_avg if hasattr(
                    edge.source, 'cost_avg') else 0) + self.calculate_rank_downward(edge.source)
            if cost > max:
                max = cost
        task.rank_downward = max
        return task.rank_downward


    def find_processor(self, task: Task, schedule):
        is_entry = len(task.t_in_edges) == 0
        if task.is_critical:
            min_eft_procId = self.critical_procId
            min_eft = task.cost_table[min_eft_procId] if task.is_entry(
            ) else sys.maxsize
            cost = task.cost_table[min_eft_procId]
            # Calculate start time
            selected_ast = est = 0 if is_entry else max(
                [edge.source.aft if edge.source.aft else 0 for edge in task.t_in_edges])
            proc_est = schedule[self.critical_procId][-1].aft if len(
                schedule[self.critical_procId]) > 0 else est
            # Check if current task and its parents are on the same processor
            undones = []
            for in_edge in task.t_in_edges:
                # parent not scheduled yet, cannot schedule this task
                if not in_edge.source.procId:
                    undones.append(in_edge.source)
                    continue
                if in_edge.source.procId-1 != self.critical_procId:
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

@delay('cpop')
class CPOPDelay(CPOP):
    pass

@reserve('cpop')
class CPOPReserve(CPOP):
    pass

@sbac('cpop')
class CPOPSBAC(CPOP):
    pass