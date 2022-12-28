import sys
from typing import Union
from algorithms.algo_base import AlgoBase
import numpy as np
from decorators import base, delay, reserve, sbac

from platforms.task import Task, MTask


@base
class HEFT(AlgoBase):
    def task_compare(self, task1: Task, task2: Task):
        # return task2.priority - task1.priority
        if task2.priority == task1.priority:
            return task2.id - task1.id
        else:
            return task2.priority - task1.priority


    def calculate_priority(self, task: Union[Task, MTask]):
        if task.priority:
            return task.priority
        max = 0
        for edge in task.out_edges:
            cost = (edge.weight if hasattr(
                edge, 'weight') else 0) + self.calculate_priority(edge.target)
            if cost > max:
                max = cost
        task.priority = (task.cost_avg if hasattr(task, 'cost_avg') else 0) + max
        return task.priority


    def find_processor(self, task: Task, schedule):
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

@delay
class HEFTDelay(HEFT):
    pass

@reserve
class HEFTReserve(HEFT):
    pass

@sbac
class HEFTSBAC(HEFT):
    pass


