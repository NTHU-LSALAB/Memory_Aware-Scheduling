import os
from graph.node import Node
from platforms.memory import Memory
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
plt.switch_backend('Agg')


class AlgoBase:
    def __init__(self, memory=Memory()):
        self.memory = memory

    def set_memory(self, memory: Memory) -> None:
        self.memory = memory

    def schedule(self, tasks: list[Node], input: int, options: dict) -> tuple[list[list[Node]], int]:
        pass

    def plot(self, schedules: list[list[Node]], makespan, filename='heft'):
        fig, ax = plt.subplots()
        per_height = 20
        gutter = 10
        height = len(schedules)*(per_height+gutter) + gutter
        for sid, schedule in enumerate(schedules):
            for slot in schedule:
                rect = Rectangle((slot.ast, sid*(per_height+gutter) + gutter), slot.aft-slot.ast,
                                 per_height, alpha=1, ec="black", fc="#FAFEFF", lw=0.5)
                fig.gca().add_patch(rect)
                rx, ry = rect.get_xy()
                cx = rx + rect.get_width()/2.0
                cy = ry + rect.get_height()/2.0

                plt.annotate(slot.id, (cx, cy), color='black',
                             fontsize=8, ha='center', va='center')
        X = [i*(per_height+gutter)+gutter+per_height /
             2 for i in range(len(schedules))]
        labels = [f'P{i+1}' for i, _ in enumerate(X)]
        ax.set_yticks(X, labels=labels)
        ax.set_xlim(0, makespan+10)
        ax.set_ylim(0, height)
        ax.set_xlabel('Time')
        ax.set_ylabel('Processor')

        ax.plot((makespan, makespan), (0, height), linestyle='dashed')
        x_ticks = np.append(ax.get_xticks(), makespan)
        ax.set_xticks(x_ticks)
        print(filename)

        if not os.path.exists('out/schedule'):
            os.mkdir('out/schedule')
        fig.savefig(f'out/schedule/{filename}.png')
        plt.close()

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
