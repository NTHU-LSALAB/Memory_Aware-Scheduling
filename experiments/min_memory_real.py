import time
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, './')
from lib.real_workflow_generator import dag_generator, parse_dax
from converter import converter
from platforms.app import App
from multiprocessing import Pool
import os
import numpy as np


task_num_list = [50, 100]
recipes = ['montage', 'cyber', 'epig', 'sight', 'inspiral']
method_list = [('heft_dalay', 'delaying', '#3c6f4f'), ('sbac',
                                                       'sbac', 'blue'), ('heft_lookup', 'reservation-based', '#edb16d')]


def worker(app, method, usage):
    last_memory = mem_size = usage
    while True:
        if mem_size <= 0:
            break

        feasible = False
        for depth in [0] if method != 'heft_lookup' else [0, 1, 2]:
            try:
                _, makepsan, memory = app.schedule(
                    method, mem_size, {"depth": depth, "plot": False})
                last_memory = memory
                if makepsan > sys.maxsize/2:
                    continue
                feasible = True
            except Exception:
                continue
        if not feasible:
            return last_memory
        mem_size -= 10

def f(method, recipe, task_num):
    start = time.time()
    app = App()
    dag_like = dag_map[recipe][task_num]
    app.read_input(dag_like, format='mb')
    _, _, usage = app.schedule('heft')

    min_data = worker(app, method[0], usage)
    end = time.time()

    print(f'{recipe} {task_num} {method[1]}: {format("%.2f" % (end-start))}, {min_data}')
    return min_data

# multi-processing
min_data_3d = []
xticks_flatlist = []
dag_map = {}
for recipe in recipes:
    tmp = {}
    for task_num in task_num_list:
        xticks_flatlist.append(f'{recipe[:4]}.-{task_num}')
        dag_like = parse_dax(recipe=recipe, task_num=task_num)
        dag_like = converter(dag_like)
        tmp[task_num] = dag_like
    dag_map[recipe] = tmp
with Pool() as p:
    min_data_list = p.starmap(
        f, [(method, recipe, task_num) for method in method_list for recipe in recipes for task_num in task_num_list])

interval = len(task_num_list) *len(recipes)
for i in range(len(method_list)):
    min_data_3d.append(min_data_list[i*interval: (i+1)*interval])

fig, ax= plt.subplots(figsize=(10, 6))
for i, data in enumerate(min_data_3d):
    ax.plot(xticks_flatlist, data, '--x', color=method_list[i][2])
ax.legend(list(map(lambda method: method[1], method_list)))
plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')

if 'latex' in os.environ:
    fig.savefig('experiments/results/real.eps',
                format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig.savefig(
        'experiments/results/real.png', bbox_inches="tight")
