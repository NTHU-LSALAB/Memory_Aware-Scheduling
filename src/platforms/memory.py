from copy import deepcopy
import shutil
from functools import cmp_to_key
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

    def __init__(self, size=100, snapshot=False):
        self.slots: list(Task) = []
        self.size = size
        self.color_map = {}
        self.total_delay = 0
        self.snapshot = snapshot
        self.snapshots = []

    def overlap_exploration(self):
        for slot in self.slots:
            overlap_slots = sorted(list(filter(
                lambda s: s.interval[0] < slot.interval[1] and s.interval[1] > slot.interval[0] and s != slot and s.addr[0] < slot.addr[0], self.slots)), key=cmp_to_key(lambda slot1, slot2: slot1.addr[1] - slot2.addr[1]))
            start = overlap_slots[-1].addr[1] if overlap_slots else 0
            slot.addr = [start, start + slot.addr[1] - slot.addr[0]]

    def map_color_addr(self, color_size: dict):
        prev_addr = 0
        for color, size in color_size.items():
            next_addr = prev_addr + size
            self.color_map[color] = [prev_addr, next_addr]
            prev_addr = next_addr

    def place_task(self, est, eft, task: Task):
        latest_start = est
        # allocate internal buffer
        buffer_ok, buffer_slot = self.place(
            task.buffer_color,
            task.buffer_size, [latest_start, latest_start + eft - est], task)
        if buffer_ok:
            latest_start = max(latest_start, buffer_slot.interval[0])
        # allocate output buffer
        output_ok, output_slot = self.place(task.output_color, task.output, [
            latest_start, latest_start + eft - est if task.is_exit() else Memory.DEADLINE], task, final=False)
        if output_ok:
            latest_start = max(latest_start, output_slot.interval[0])

        if output_ok and buffer_ok:
            return latest_start, latest_start+eft-est, True
        else:
            self.rollback(task.id)
            if not isinstance(output_slot, Slot):
                # print('task', task.id, 'subscribe to', output_slot.id)
                output_slot.subscribers.append(task)
                task.topics.append(output_slot)
            if not isinstance(buffer_slot, Slot):
                # print('task', task.id, 'subscribe to', buffer_slot.id)
                buffer_slot.subscribers.append(task)
                task.topics.append(buffer_slot)
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
            # print(colorSlots)
        # print(task.id, 'et', et, 'color:', color)
        if et >= sys.maxsize:
            return False, colorSlots[latest_id].task
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
            self.total_delay += delay_to - interval[0]
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
            self.total_delay += delay_to - interval[0]
            interval = [delay_to, delay_to + (interval[1] - interval[0])]
            return self.best_fit(size, interval, task, final)
        else:
            return False, None

    def rollback(self, tid: int):
        self.slots = list(filter(lambda slot: slot.task.id !=
                          tid, self.slots))

    def free_tensor(self, task, until):
        if hasattr(task, 'mId'):
            target_slots = list(
                filter(lambda slot: slot.task.mId is task.mId and slot.final is False, self.slots))
        else:
            target_slots = list(
                filter(lambda slot: slot.task is task and slot.final is False, self.slots))
        if target_slots:
            target_slot = target_slots[0]
            target_slot.interval[1] = until
            target_slot.final = True
        if self.snapshot:
            self.snapshots.append(deepcopy(self.slots))

    def allocate(self, address, interval, task, final=True, color=None):
        # insert slot
        new_slot = Slot(address, interval, task, final, color)
        bisect.insort(self.slots, new_slot)
        if self.snapshot:
            self.snapshots.append(deepcopy(self.slots))
        return new_slot

    def max(self):
        return max(list(map(lambda slot: slot.addr[1], self.slots)))

    def plot(self, makespan=None, filename='allocation', slots=None):
        fig, ax = plt.subplots()
        slots = slots if slots else self.slots
        for slot in slots:
            if slot.size == 0:
                continue
            rect = Rectangle(slot.pos, slot.length,
                             slot.size, alpha=1, ec="black", fc="#FAFEFF", lw=0.5)
            fig.gca().add_patch(rect)
            rx, ry = rect.get_xy()
            cx = rx + (rect.get_width() /
                       2.0 if slot.interval[1] <= makespan else 5)
            cy = ry + rect.get_height()/2.0

            # print(slot.task.id sif slot.task else 'I', slot.pos, slot.length, slot.size)
            plt.annotate(('B' if slot.is_buffer else 'O') + (str(slot.task.mId) if hasattr(slot.task, 'mId') else str(slot.task.id)), (cx, cy), color='black',
                         fontsize=8, ha='center', va='center')
        ax.set_ylim(0, self.max() + 10)
        ax.set_xlim(0, makespan+10 if makespan else self.DEADLINE)
        ax.set_xlabel('Time')
        ax.set_ylabel('Address')
        if self.size is not sys.maxsize:
            ax.axhline(y=self.size, color='red', linestyle='dashed')
            y_ticks = np.append(ax.get_yticks(), self.size)
            ax.set_yticks(y_ticks)

        if makespan:
            ax.axvline(x=makespan, linestyle='dashed')
            x_ticks = np.append(ax.get_xticks(), makespan)
            ax.set_xticks(x_ticks)

        if not os.path.exists('out/memory'):
            os.mkdir('out/memory')
        if 'latex' in os.environ:
            fig.savefig(f'out/memory/{filename}.eps', format="eps",
                        dpi=1200, bbox_inches="tight", transparent=True)
        else:
            fig.savefig(f'out/memory/{filename}.png')
        plt.close()

    def plot_snapshot(self, makespan=None, filename='allocation'):
        if os.path.exists(f'out/memory/{filename}'):
            shutil.rmtree(f'out/memory/{filename}')
        os.mkdir(f'out/memory/{filename}')
        for i, snapshot in enumerate(self.snapshots):
            self.plot(makespan, f'{filename}/snapshot{i+1}', snapshot)


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
        id = self.task.mId if hasattr(self.task, 'mId') else (
            self.task.id if self.task else 'IO')
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
