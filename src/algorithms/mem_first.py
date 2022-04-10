from functools import cmp_to_key
import random
import sys
from algorithms.algo_base import AlgoBase
from algorithms.heft import calculate_priority, find_processor, task_compare

from platforms.memory import Memory
from platforms.task import Task


class MemFirst(AlgoBase):

    def schedule(self, tasks: list[Task], input, options={}) -> tuple[list[list[Task]], int]:
        # print('HEFT')
        self.input = input
        self.tasks = tasks
        makespan = 0
        entry_task = next(
            (task for task in tasks if len(task.in_edges) == 0), None)
        exit_task = next(
            (task for task in tasks if len(task.out_edges) == 0), None)

        if entry_task is None or exit_task is None:
            raise ValueError('No entry or exit node')

        calculate_priority(entry_task)
        self.color_graph(entry_task)
        color_size = self.decide_color_size()
        self.memory.map_color_addr(color_size)

        sorted_tasks = sorted(tasks, key=cmp_to_key(task_compare))
        # self.color_graph2(sorted_tasks)
        # color_size = self.decide_color_size()
        # self.memory.map_color_addr(color_size)

        schedule: list[list[Task]] = [[]
                                      for _ in range(len(entry_task.cost_table))]

        for task in sorted_tasks:
            est, eft, pid = find_processor(task, schedule)
            # print(est, eft)

            # allocate input tensor
            if task is entry_task:
                self.memory.place(
                    self.input_color,
                    input, [est, eft], task)

            # latest_start = est
            ast, aft, cool = self.memory.place_task(est, eft, task)
            # # allocate output tensor
            # slot = self.memory.place(task.output_color, task.output, [
            #     est, eft if task.is_exit() else Memory.DEADLINE], task, final=False)
            # if slot:
            #     latest_start = max(latest_start, slot.interval[0])
            # # print(latest_start, eft, est)
            # # allocate internal buffer
            # slot = self.memory.place(
            #     task.buffer_color,
            #     task.buffer_size, [latest_start, latest_start + eft - est], task)
            # if slot:
            #     latest_start = max(latest_start, slot.interval[0])

            # # Now we know the ast, aft
            # ast = latest_start
            # aft = latest_start + eft - est

            if not cool:
                continue
            # free input tensors
            if not task.is_entry():
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
            if task.aft > makespan:
                makespan = task.aft

            # run subscribers
            for sub in task.subscribers:
                ast, aft, cool = self.memory.place_task(est, eft, sub)
                # free input tensors
                if not task.is_entry() and cool:
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
                if task.aft > makespan:
                    makespan = task.aft

        self.memory.plot(makespan, 'mem-first')
        self.plot(schedule, makespan, 'mem-first')
        return schedule, makespan, self.memory.max()

    def print_priority(self, entry_node: Task):
        print('''UPPER RANKS
---------------------------
Task    Rank
---------------------------''')
        self.bfs(entry_node, op=lambda task: print(
            f'{task.id}       {round(task.priority, 4)}'))

    def color_graph2(self, tasks):
        self.color_pool = set()
        self.free_color_list = []
        self.mem_size = 100
        self.input_color = self.pick_color()
        for task in tasks:
            self.color_task(task)

    def color_graph(self, entry_node: Task):
        self.color_pool = set()
        self.free_color_list = []
        self.mem_size = 100
        self.input_color = self.pick_color()
        self.bfs(entry_node, op=self.color_task)

    def color_task(self, task: Task):
        if task.buffer_color and task.output_color:
            return
        # print('free color:', self.free_color_list)
        buffer_color = self.pick_color()
        output_color = self.pick_color()
        # print('color', task.id, 'with color:',
        #       f'b\'{buffer_color}', f'o\'{output_color}')
        task.buffer_color = buffer_color
        task.output_color = output_color
        self.free_color_list.append(task.buffer_color)
        # Release input color
        if task.is_entry():
            self.free_color_list.append(self.input_color)
        else:
            for in_edge in task.in_edges:
                last_use = True
                for out_edge in in_edge.source.out_edges:
                    if out_edge.target is task:
                        continue
                    if out_edge.target.buffer_color is None:  # not allocate yet
                        last_use = False
                        break
                if last_use:
                    self.free_color_list.append(in_edge.source.output_color)

    def generate_color(self):
        color = "#"+''.join([random.choice('0123456789ABCDEF')
                             for _ in range(6)])
        while color in self.color_pool:
            color = "#"+''.join([random.choice('0123456789ABCDEF')
                                 for _ in range(6)])
        self.color_pool.add(color)
        return color

    def pick_color(self):
        if not self.free_color_list:
            return self.generate_color()
        else:
            return self.free_color_list.pop(0)

    def decide_color_size(self):
        color_sizes = {}
        color_sizes[self.input_color] = self.input

        def update(color, size):
            if color in color_sizes:
                color_sizes[color] = max(size, color_sizes[color])
            else:
                color_sizes[color] = size
        for task in self.tasks:
            update(task.buffer_color, task.buffer_size)
            update(task.output_color, task.output)

        return color_sizes
