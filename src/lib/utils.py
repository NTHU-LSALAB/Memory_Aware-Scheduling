import matplotlib.pyplot as plt
import numpy as np

from platforms.task import Task
from platforms.dep import Dep


def print_schedule(schedule, makespan, version=''):
    print(f'''HEFT {version} SCHEDULE
---------------------------
Proc	Task	AST	AFT
---------------------------''')
    for sid, s in enumerate(schedule):
        for slot in s:
            print(f'{sid+1}\t{slot.id:<2}\t{slot.ast:<2}\t{slot.aft:<2}')
    print(f'''---------------------------
Makespan = {makespan}
---------------------------
END
---------------------------''')


def calculate_idle_time(schedule, makespan):
    processor_num = len(schedule)
    idle_time = 0
    for p in range(processor_num):
        for sid, slot in enumerate(schedule[p]):
            if sid == 0:
                idle_time += slot.ast
            else:
                idle_time += slot.ast - schedule[p][sid - 1].aft
            if sid == len(schedule[p]) - 1:
                idle_time += makespan - slot.aft

    return format(idle_time / processor_num, '.2f')


def get_parallelism_degree(schedule, makespan):
    processor_num = len(schedule)
    counter = [0 for _ in schedule]
    busy_time = 0
    for t in range(makespan):
        busy_count = 0
        for p in range(processor_num):
            if t >= schedule[p][counter[p]].ast and t <= schedule[p][counter[p]].aft:
                busy_count += 1

            if t == schedule[p][counter[p]].aft and counter[p] < len(schedule[p]) - 1:
                counter[p] += 1

        busy_time += busy_count

    return format(busy_time/makespan, '.2f')


def get_parallelism_minmax(schedule, makespan):
    minp = maxp = 1
    processor_num = len(schedule)
    counter = [0 for _ in schedule]
    data = []
    for t in range(makespan):
        busy_count = 0
        for p in range(processor_num):
            if t >= schedule[p][counter[p]].ast and t <= schedule[p][counter[p]].aft:
                busy_count += 1

            if t == schedule[p][counter[p]].aft and counter[p] < len(schedule[p]) - 1:
                counter[p] += 1

        if busy_count > maxp:
            maxp = busy_count
    return minp, maxp


def show_parallelsim_degree(schedule, makespan):
    processor_num = len(schedule)
    counter = [0 for _ in schedule]
    data = []
    for t in range(makespan):
        busy_count = 0
        for p in range(processor_num):
            if t >= schedule[p][counter[p]].ast and t <= schedule[p][counter[p]].aft:
                busy_count += 1

            if t == schedule[p][counter[p]].aft and counter[p] < len(schedule[p]) - 1:
                counter[p] += 1
        data.append(busy_count)
    return data


def diff(base, value):
    if isinstance(base, str):
        base = float(base)
    if isinstance(value, str):
        value = float(value)
    return format(100*(value - base) / base, '.2f')


def ssse(tasks):
    entry_tasks = list(filter(lambda task: task.is_entry(), tasks))
    exit_tasks = list(filter(lambda task: task.is_exit(), tasks))

    if len(entry_tasks) == 0 or len(exit_tasks) == 0:
        raise ValueError('No entry or exit nodes')

    if len(entry_tasks) > 1:
        entry_task = Task(0, [0, 0, 0], 0, 0)
        tasks.insert(0, entry_task)
        for task in entry_tasks:
            edge = Dep(entry_task, task, 0, 0)
            entry_task.out_edges.append(edge)
            task.in_edges.append(edge)
    else:
        entry_task = entry_tasks[0]

    if len(exit_tasks) > 1:
        exit_task = Task(len(tasks), [0, 0, 0], 0, 0)
        tasks.append(exit_task)
        for task in exit_tasks:
            edge = Dep(task, exit_task, 0, 0)
            task.out_edges.append(edge)
            exit_task.in_edges.append(edge)
    else:
        exit_task = exit_tasks[0]

    return entry_task, exit_task
