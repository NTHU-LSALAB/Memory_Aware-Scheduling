from functools import cmp_to_key
import random
import sys
from algorithms.algo_base import AlgoBase
from algorithms.heft import calculate_priority, find_processor, task_compare

from platforms.memory import Memory
from platforms.task import Task


class MemFirst(AlgoBase):

    def schedule(self, tasks: list[Task], input, options={}, format='default') -> tuple[list[list[Task]], int]:
        # print('HEFT')
        self.input = input
        self.input_color = None
        self.tasks = tasks
        self.makespan = 0
        entry_task = next(
            (task for task in tasks if len(task.in_edges) == 0), None)
        exit_task = next(
            (task for task in tasks if len(task.out_edges) == 0), None)

        if entry_task is None or exit_task is None:
            raise ValueError('No entry or exit node')

        calculate_priority(entry_task)
        self.color_graph(entry_task)
        color_size, _ = self.decide_color_size()
        # print(color_size)
        self.memory.map_color_addr(color_size)

        sorted_tasks = sorted(tasks, key=cmp_to_key(task_compare))

        self.schedule: list[list[Task]] = [[]
                                           for _ in range(len(entry_task.cost_table))]

        for task in sorted_tasks:
            self.schedule_task(task)

        self.overlap_exploration()
        if options.get('plot', True):
            self.memory.plot(self.makespan, 'mem-first')
            self.plot(self.schedule, self.makespan, 'mem-first')
        
        for task in self.tasks:
            if not task.procId:
                raise ValueError('Fail to schedule')
        if self.memory.max() > self.memory.size:
            raise ValueError('Fail to schedule')

        return self.schedule, self.makespan, self.memory.max()

    def schedule_task(self, task: Task):
        try:
            est, eft, pid = find_processor(task, self.schedule)
        except Exception as e:
            for parent in e.args[0]:
                # print(task.id, 'subscribe to', parent.id)
                parent.subscribers.append(task)
                task.topics.append(parent)
            return

        # allocate input tensor
        if task.is_entry():
            self.memory.place(
                self.input_color,
                self.input, [est, eft], task)

        ast, aft, cool = self.memory.place_task(est, eft, task)

        if not cool:
            return
        # print('schedule', task.id, ast, aft)
        # free input tensors
        subscribers = []
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
                    # print(task.id, 'free', in_edge.source.id)
                    for sub in in_edge.source.subscribers:
                        sub.topics = list(
                            filter(lambda topic: topic.id != in_edge.source.id, sub.topics))
                        if len(sub.topics) == 0:
                            subscribers.append(sub)
        task.procId = pid + 1
        task.ast = ast
        task.aft = aft
        self.schedule[pid].append(task)
        if task.aft > self.makespan:
            self.makespan = task.aft
        # notify subscribers
        for sub in subscribers:
            self.schedule_task(sub)
    
    def overlap_exploration(self):
        self.memory.overlap_exploration()

    def color_graph(self, entry_node: Task):
        self.color_pool = set()
        self.free_color_list = []
        self.mem_size = 100
        self.input_color = self.pick_color(self.input)
        self.bfs(entry_node, op=self.color_task)

    def color_task(self, task: Task):
        if task.buffer_color and task.output_color:
            return
        # print('free color:', self.free_color_list)
        buffer_color = self.pick_color(task.buffer_size)
        task.buffer_color = buffer_color
        output_color = self.pick_color(task.output)
        task.output_color = output_color
        # print('color', task.id, 'with color:',
        #       f'b\'{buffer_color}', f'o\'{output_color}')
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

    def pick_color(self, size):
        _, usage = self.decide_color_size()
        if not self.free_color_list:
            # if usage + size > self.memory.size:
            #     raise ValueError('Fail to allocate memory!!')
            return self.generate_color()
        else:
            # if usage + size <= self.memory.size:
            #     return self.generate_color()
            # # best fit
            # min_size = self.memory.size
            # min_id = -1
            # for i, color in enumerate(self.free_color_list):
            #     color_sizes, _ = self.decide_color_size()
            #     color_size = color_sizes[color]
            #     if color_size < min_size and color_size >= size:
            #         min_size = color_size
            #         min_id = i
            # if min_id == -1:
            #     raise ValueError('Fail to allocate memory!!')
            return self.free_color_list.pop(0)

    def decide_color_size(self):
        color_sizes = {}
        if not self.input_color:
            return color_sizes, 0
        color_sizes[self.input_color] = self.input
        self.usage = self.input

        def update(color, size):
            if not color:
                return
            if color in color_sizes:
                larger = max(size, color_sizes[color])
                self.usage += larger - color_sizes[color]
                color_sizes[color] = larger
            else:
                color_sizes[color] = size
                self.usage += size
        for task in self.tasks:
            update(task.buffer_color, task.buffer_size)
            update(task.output_color, task.output)

        return color_sizes, self.usage
