import os
from graph.node import Node
from platforms.memory import Memory
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np


class AlgoBase:
    def __init__(self, memory=Memory()):
        self.memory = memory

    def set_memory(self, memory: Memory) -> None:
        self.memory = memory

    def schedule(self, tasks: list[Node], input: int, output: int) -> tuple[list[list[Node]], int]:
        pass
    
    def plot(self, schedules: list[list[Node]], makespan, filename='heft'):
        fig, ax = plt.subplots()
        per_height = 20
        gutter = 10
        height = len(schedules)*(per_height+gutter) + gutter
        for sid, schedule in enumerate(schedules):
            for slot in schedule:
                rect = Rectangle((slot.ast, sid*(per_height+gutter) + gutter), slot.aft-slot.ast,
                                 per_height, alpha=1, color='black', fill=None)
                fig.gca().add_patch(rect)
                rx, ry = rect.get_xy()
                cx = rx + rect.get_width()/2.0
                cy = ry + rect.get_height()/2.0

                plt.annotate(slot.id, (cx, cy), color='black', weight='bold',
                             fontsize=12, ha='center', va='center')
        plt.ylim(0, height)
        plt.xlim(0, makespan+10)

        plt.plot((makespan, makespan), (0, height), linestyle='dashed')
        x_ticks = np.append(ax.get_xticks(), makespan)
        ax.set_xticks(x_ticks)

        if not os.path.exists('schedule'):
            os.mkdir('schedule')
        plt.savefig(f'schedule/{filename}.png')

    def bfs(self, entry_task: Node, op=None):

        visited = [entry_task]
        queue = [entry_task]

        while(queue):
            task = queue.pop(0)
            if op:
                op(task)
            for edge in task.out_edges:
                if edge.target not in visited:
                    visited.append(edge.target)
                    queue.append(edge.target)


class Slot:
    task: Node
    ast: int
    aft: int
