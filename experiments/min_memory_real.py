import time
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, './')
from lib.real_workflow_generator import parse_dax, save_dag
from converter import converter
from platforms.app import App
from multiprocessing import Pool
import os
import numpy as np

task_num_list = [50, 100, 200]
recipes = ['Mont', 'Cyb', 'Epig', 'SIGHT', 'LIGO']
method_list = [('heft_delay', 'delaying', '#00994c', ''), ('sbac',
                                                       'sbac', '#004C99', ''), ('heft_lookup', 'reservation-based', '#edb16d', '--x')]


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

    print(f'{recipe} {task_num} {method[1]}: {format("%.2f" % (end-start))}')
    return min_data

# multi-processing
min_data_3d = []
xticks_flatlist = []
dag_map = {}
for recipe in recipes:
    tmp = {}
    for task_num in task_num_list:
        xticks_flatlist.append(f'{recipe}.-{task_num}')
        # dag_like = parse_dax(recipe=recipe, task_num=task_num)
        # dag_like = converter(dag_like)
        # save_dag(dag_like, f'./experiments/data/real/{recipe}.-{task_num}.json')
        # tmp[task_num] = dag_like
        tmp[task_num] = f'./experiments/data/real/{recipe}.-{task_num}.json'
    dag_map[recipe] = tmp
with Pool() as p:
    min_data_list = p.starmap(
        f, [(method, recipe, task_num) for method in method_list for recipe in recipes for task_num in task_num_list])

interval = len(task_num_list) *len(recipes)
for i in range(len(method_list)):
    min_data_3d.append(min_data_list[i*interval: (i+1)*interval])

fig, ax= plt.subplots(figsize=(15, 6))

bar_width = 0.2
X = br = np.arange(len(xticks_flatlist))
for i, data in enumerate(min_data_3d):
    ax.bar(br, data, width=bar_width, color=method_list[i][2], ec='#333')
    br = [x + bar_width for x in br]
    # ax.plot(xticks_flatlist, data, method_list[i][3], color=method_list[i][2], linewidth=1)
ax.set_xticks(X + bar_width, labels=xticks_flatlist)
ax.legend(list(map(lambda method: method[1], method_list)))
ax.set_ylabel('Minimum memory', fontsize=14)
plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')

if 'latex' in os.environ:
    fig.savefig(
        'experiments/results/real_result.pdf', bbox_inches="tight")
else:
    fig.savefig(
        'experiments/results/real_result.png', bbox_inches="tight")
