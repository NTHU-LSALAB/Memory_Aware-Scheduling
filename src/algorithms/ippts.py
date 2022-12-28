import sys
from algorithms.algo_base import AlgoBase
import numpy as np
from decorators import base, delay, reserve, sbac

from platforms.task import Task

@base('ippts')
class IPPTS(AlgoBase):

    def task_compare(self, task1: Task, task2: Task):
        return task2.priority - task1.priority


    def calculate_priority(self, task: Task):
        self.calculate_pcm(task)
        for t in self.tasks:
            self._calculate_priority(t)

    def _calculate_priority(self, task: Task):
        if task.priority:
            return task.priority
        rank_pcm = np.average(task.pcm)
        p_rank = rank_pcm * len(task.out_edges)
        task.priority = p_rank
        return task.priority

    def calculate_pcm(self, task: Task):

        if task.pcm[0]:
            return task.pcm

        for i in range(len(task.cost_table)):
            max = task.cost_table[i]
            for edge in task.out_edges:
                min = sys.maxsize
                for cid, cost in enumerate(edge.target.cost_table):
                    pcm = self.calculate_pcm(edge.target)
                    tmp = pcm[cid] + task.cost_table[cid] + \
                        cost + (edge.weight if i != cid else 0)
                    if tmp < min:
                        min = tmp
                if min > max:
                    max = min
            task.pcm[i] = max
        return task.pcm


    def find_processor(self, task: Task, schedule):
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

@delay('ippts')
class IPPTSDelay(IPPTS):
    pass

@reserve('ippts')
class IPPTSReserve(IPPTS):
    pass

@sbac('ippts')
class IPPTSSBAC(IPPTS):
    pass