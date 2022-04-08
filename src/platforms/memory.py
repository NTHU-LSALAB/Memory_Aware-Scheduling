import bisect
import os
import random
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

from platforms.task import Task

class Memory:
    DEADLINE = 200

    def __init__(self, size=100):
        self.slots = []
        self.size = size

    def first_fit(self, size, interval, task: Task, final=True, can_delay = True):
        if size == 0:
            return True, None
        overlap_slots = list(filter(
            lambda slot: slot.interval[0] < interval[1] and slot.interval[1] > interval[0], self.slots))
        if not overlap_slots:
            return True, self.allocate((0, size), interval, task, final)

        prev_addr = 0
        for slot in overlap_slots:
            if (slot.addr[0] - prev_addr) >= size:
                return True, self.allocate([prev_addr, prev_addr+size],
                                           interval, task, final)
            prev_addr = max(slot.addr[1], prev_addr)
        if (self.size - prev_addr) >= size:
            return True, self.allocate([prev_addr, prev_addr+size], interval, task, final)
        if can_delay:
            # delay
            delay_to = min([slot.interval[1] for slot in overlap_slots])
            if delay_to == self.DEADLINE:
                return False, None
            interval = [delay_to, delay_to + (interval[1] - interval[0])]
            return self.first_fit(size, interval, task, final, can_delay)
        else:
            return False, None

    def best_fit(self, size, interval, task, final=True):
        if size == 0:
            return True, None
        overlap_slots = list(filter(
            lambda slot: slot.interval[0] < interval[1] and slot.interval[1] > interval[0], self.slots))
        if not overlap_slots:
            return True, self.allocate((0, size), interval, task, final)

        prev_addr = 0
        for slot in overlap_slots:
            if (slot.addr[0] - prev_addr) >= size:
                return True, self.allocate([prev_addr, prev_addr+size],
                                           interval, task, final)
            prev_addr = max(slot.addr[1], prev_addr)
        if (self.size - prev_addr) >= size:
            return True, self.allocate([prev_addr, prev_addr+size], interval, task, final)
        # delay
        delay_to = min([slot.interval[1] for slot in overlap_slots])
        if delay_to == self.DEADLINE:
            return False, None
        interval = [delay_to, delay_to + (interval[1] - interval[0])]
        return self.first_fit(size, interval, task, final)

    def rollback(self, tid: int):
        self.slots = list(filter(lambda slot: slot.task.id !=
                          tid, self.slots))

    def free_tensor(self, task, until):
        target_slots = list(
            filter(lambda slot: slot.task is task and slot.final is False, self.slots))
        if target_slots:
            target_slot = target_slots[0]
            target_slot.interval[1] = until
            target_slot.final = True

    def allocate(self, address, interval, task, final=True):
        # insert slot
        new_slot = Slot(address, interval, task, final)
        bisect.insort(self.slots, new_slot)
        return new_slot
    
    def max(self):
        return max(list(map(lambda slot: slot.addr[1], self.slots)))

    def plot(self, makespan=None, filename='allocation'):
        fig, ax = plt.subplots()
        for slot in self.slots:
            if slot.size == 0:
                continue
            color = "#"+''.join([random.choice('0123456789ABCDEF')
                                for j in range(6)])
            rect = Rectangle(slot.pos, slot.length,
                             slot.size, alpha=1, color=color)
            fig.gca().add_patch(rect)
            rx, ry = rect.get_xy()
            cx = rx+4
            cy = ry + rect.get_height()/2.0

            # print(slot.task.id sif slot.task else 'I', slot.pos, slot.length, slot.size)
            plt.annotate(str(slot.task.id) + ('(B)' if slot.is_buffer else '(O)'), (cx, cy), color='w', weight='bold',
                         fontsize=12, ha='center', va='center')
        plt.ylim(0, self.size)
        plt.xlim(0, makespan+10 if makespan else self.DEADLINE)
        if makespan:
            plt.plot((makespan, makespan), (0, self.size), linestyle='dashed')
            x_ticks = np.append(ax.get_xticks(), makespan)
            ax.set_xticks(x_ticks)

        if not os.path.exists('out/memory'):
            os.mkdir('out/memory')
        plt.savefig(f'out/memory/{filename}.png')


class Slot:
    def __init__(self, address, interval, task, final=True):
        self.addr = address
        self.interval = interval
        self.task = task
        self.final = final
        self.is_buffer = final

    @property
    def pos(self):
        return (self.interval[0], self.addr[0])

    @property
    def length(self):
        return self.interval[1] - self.interval[0]

    @property
    def size(self):
        return self.addr[1] - self.addr[0]

    def __lt__(self, other):
        return self.addr[0] < other.addr[0]

    def __repr__(self):
        id = self.task.id if self.task else 'IO'
        # return f'\n(id: {id}, final: {self.final}, round: {self.task.round})'
        # return f'\n(id: {id}, start: {self.addr[0]}, end: {self.addr[1]})'
        return f'\n(id: {id}, start: {self.interval[0]}, end: {self.interval[1]})'
