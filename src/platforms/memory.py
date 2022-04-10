from platforms.task import Task
import bisect
import os
import random
import sys
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
plt.switch_backend('Agg')


class Memory:
    DEADLINE = sys.maxsize

    def __init__(self, size=100):
        self.slots: list(Task) = []
        self.size = size
        self.color_map = {}

    def map_color_addr(self, color_size: dict):
        prev_addr = 0
        for color, size in color_size.items():
            next_addr = prev_addr + size
            self.color_map[color] = [prev_addr, next_addr]
            prev_addr = next_addr

    def place_task(self, est, eft, task):
        latest_start = est
        output_ok, slot = self.place(task.output_color, task.output, [
            est, eft if task.is_exit() else Memory.DEADLINE], task, final=False)
        if slot:
            latest_start = max(latest_start, slot.interval[0])
        # print(latest_start, eft, est)
        # allocate internal buffer
        buffer_ok, slot = self.place(
            task.buffer_color,
            task.buffer_size, [latest_start, latest_start + eft - est], task)
        if slot:
            latest_start = max(latest_start, slot.interval[0])

        if output_ok and buffer_ok:
            return latest_start, latest_start+eft-est, True
        else:
            self.rollback(task.id)
            return None, None, False

    def place(self, color, size, interval, task, final=True):
        if color not in self.color_map:
            raise ValueError('Color not found!')
        addr = self.color_map[color]
        # print('task', task.id, 'color', color, [addr[0], addr[0] + size])
        colorSlots = list(filter(lambda slot: slot.color == color, self.slots))
        if not colorSlots:
            et = 0
        else:
            latest_id = np.argmax(
                list(map(lambda slot: slot.interval[1], colorSlots)))
            et = colorSlots[latest_id].interval[1]
        # print(et)
        if et == sys.maxsize:
            # print(task.id, self.slots[latest_id].task.id)
            self.slots[latest_id].task.subscribers.append(
                Subscriber(color, size, interval, task, final))
            return False, None
        if interval[0] < et:
            interval = [et, et + interval[1] - interval[0]]
        return True, self.allocate([addr[0], addr[0] + size], interval, task, final, color)

    def fit(self, size, interval, task: Task, final=True, can_delay=True, mode='best'):
        if mode == 'first':
            return self.first_fit(size, interval, task, final, can_delay)
        else:
            return self.best_fit(size, interval, task, final, can_delay)

    def first_fit(self, size, interval, task, final=True, can_delay=True):
        if size == 0:
            return True, None
        overlap_slots = list(filter(
            lambda slot: slot.interval[0] < interval[1] and slot.interval[1] > interval[0], self.slots))
        if not overlap_slots:
            return True, self.allocate((0, size), interval, task, final)

        free_list = []
        prev_addr = 0
        for slot in overlap_slots:
            if (slot.addr[0] - prev_addr) >= size:
                free_list.append([prev_addr, slot.addr[0]])
            prev_addr = max(slot.addr[1], prev_addr)
        if (self.size - prev_addr) >= size:
            free_list.append([prev_addr, self.size])
        if free_list:
            # return first fittable slot
            start_at = free_list[0][0]
            return True, self.allocate([start_at, start_at+size], interval, task, final)
        if can_delay:
            # delay
            delay_to = min([slot.interval[1] for slot in overlap_slots])
            if delay_to == self.DEADLINE:
                return False, None
            interval = [delay_to, delay_to + (interval[1] - interval[0])]
            return self.first_fit(size, interval, task, final, can_delay)
        else:
            return False, None

    def best_fit(self, size, interval, task, final=True, can_delay=True):
        if size == 0:
            return True, None
        overlap_slots = list(filter(
            lambda slot: slot.interval[0] < interval[1] and slot.interval[1] > interval[0], self.slots))
        if not overlap_slots:
            return True, self.allocate((0, size), interval, task, final)

        free_list = []
        prev_addr = 0
        for slot in overlap_slots:
            if (slot.addr[0] - prev_addr) >= size:
                free_list.append([prev_addr, slot.addr[0]])
            prev_addr = max(slot.addr[1], prev_addr)

        if (self.size - prev_addr) >= size:
            free_list.append([prev_addr, self.size])
        if free_list:
            min_size = free_list[0][1] - free_list[0][0]
            min_id = 0
            for i, slot in enumerate(free_list):
                slot_size = slot[1] - slot[0]
                if slot_size < min_size:
                    min_size = slot_size
                    min_id = i
            start_at = free_list[min_id][0]
            return True, self.allocate([start_at, start_at+size], interval, task, final)

        if can_delay:
            # delay
            delay_to = min([slot.interval[1] for slot in overlap_slots])
            if delay_to == self.DEADLINE:
                return False, None
            interval = [delay_to, delay_to + (interval[1] - interval[0])]
            return self.best_fit(size, interval, task, final)
        else:
            return False, None

    def rollback(self, tid: int):
        self.slots = list(filter(lambda slot: slot.task.id !=
                          tid, self.slots))

    def free_tensor(self, task: Task, until):
        target_slots = list(
            filter(lambda slot: slot.task is task and slot.final is False, self.slots))
        if target_slots:
            target_slot = target_slots[0]
            target_slot.interval[1] = until
            target_slot.final = True

    def allocate(self, address, interval, task, final=True, color=None):
        # insert slot
        new_slot = Slot(address, interval, task, final, color)
        bisect.insort(self.slots, new_slot)
        return new_slot

    def max(self):
        return max(list(map(lambda slot: slot.addr[1], self.slots)))

    def plot(self, makespan=None, filename='allocation'):
        print(self.slots)
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
        ax.set_ylim(0, self.size)
        ax.set_xlim(0, makespan+10 if makespan else self.DEADLINE)
        ax.set_xlabel('Time')
        ax.set_ylabel('Address')

        if makespan:
            ax.plot((makespan, makespan), (0, self.size), linestyle='dashed')
            x_ticks = np.append(ax.get_xticks(), makespan)
            ax.set_xticks(x_ticks)

        if not os.path.exists('out/memory'):
            os.mkdir('out/memory')
        fig.savefig(f'out/memory/{filename}.png')
        plt.close()


class Slot:
    def __init__(self, address, interval, task: Task, final=True, color=None):
        self.addr = address
        self.interval = interval
        self.task = task
        self.final = final
        self.is_buffer = final
        self.color = color

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
        return f'\n(id: {id}, start: {self.interval[0]}, end: {self.interval[1]}, addr: ({self.addr[0]}, {self.addr[1]}))'


class Subscriber():
    def __init__(self, color, size, interval, task, final):
        self.color = color
        self.size = size
        self.interval = interval
        self.task = task
        self.final = final
