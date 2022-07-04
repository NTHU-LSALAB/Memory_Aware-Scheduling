import matplotlib.pyplot as plt
import numpy as np

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
