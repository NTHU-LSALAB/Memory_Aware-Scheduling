import json
from multiprocessing import Pool
import os
import sys
sys.path.insert(0, 'src')
from lib.utils import get_parallelism_degree
import matplotlib.pyplot as plt
from platforms.app import App
from lib.rand_workflow_generator import workflows_generator
import numpy as np

app = App()

depth_list = [0, 1, 2, 3, 4, 5]

iterations = 100


def worker(app, depth, usage):
    last_memory = mem_size = usage
    while True:
        if mem_size <= 0:
            break
        try:
            _, makepsan, memory = app.schedule(
                'heft_reserve', mem_size, {"depth": depth, "plot": False})
            last_memory = memory
            if makepsan > sys.maxsize/2:
                return last_memory
        except Exception:
            return last_memory
        mem_size -= 10

def f(depth):
    dag_like = workflows_generator()
    app.read_input(dag_like)
    _, _, usage = app.schedule('heft')
    try:
        schedule, makespan, _ = app.schedule('heft_reserve', usage, {"depth": depth})
        min_memory = worker(app, depth, usage)
        return get_parallelism_degree(schedule, makespan), min_memory
    except:
        pass

if os.path.exists('./experiments/results/depth_statistics.json'):
    with open('./experiments/results/depth_statistics.json', 'r') as f:
        result = json.load(f)
        para_list = result['para']
        min_memory_list = result['min_memory']
else:
    data = [[] for _ in depth_list]
    min_memory_list = [[] for _ in depth_list]
    para_list = [[] for _ in depth_list]
    for i, depth in enumerate(depth_list):
        with Pool() as p:
            data[i] = p.starmap(f, [[depth] for _ in range(iterations)])
            para_list[i] = list(map(lambda d: d[0], filter(lambda d: d != None, data[i])))
            min_memory_list[i] = list(map(lambda d: d[1], filter(lambda d: d != None, data[i])))

    with open('./experiments/results/depth_statistics.json', 'w') as f:
        json.dump({
            'para': para_list,
            'min_memory': min_memory_list
        }, f, indent=4)
            

fig, ax = plt.subplots(figsize=(8, 3.5))
ax2 = ax.twinx()
X = np.arange(len(depth_list))
br = 0.3
bplot = ax.boxplot(para_list, vert=True, positions=X, showfliers=False, # vertical box alignment
                           patch_artist=True, boxprops=dict(facecolor=(0, 0, 0, 0)), whiskerprops=dict(linestyle='dashed', linewidth=1.0, color='#333'), medianprops=dict(color='#ff3333'), capprops=dict(color='#333'), widths=.2)

mplot = ax2.boxplot(min_memory_list, vert=True, positions=X+br, showfliers=False,  # vertical box alignment
                           patch_artist=True, boxprops=dict(facecolor=(0, 1, 0, 0)), whiskerprops=dict(linestyle='dashed', linewidth=1.0, color='#333'), medianprops=dict(color='#ff3333'), capprops=dict(color='#333'), widths=.2)
ax.set_xticks(X+0.15, labels=depth_list)
ax.set_xlabel('Depth', fontsize=14)
ax.set_ylabel('Degree of parallelism (# processor)', fontsize=14)
ax2.set_ylabel('Minimum memory', color='blue', fontsize=14)

for mbox, box, mmedian, median in zip(mplot['boxes'], bplot['boxes'], mplot['medians'], bplot['medians']):
    # box.set_edgecolor('orange')
    mbox.set_edgecolor('blue')
    (x_l, y), (x_r, _) = median.get_xydata()

    # ax.text(x_l - 0.02, y,
    #         '%.2f' % y,
    #         va='center',
    #         ha='right',
    #         fontsize=8)

    (x_l, y), (x_r, _) = mmedian.get_xydata()

    # ax2.text(x_r + 0.02, y,
    #         '%d' % y,
    #         va='center',
    #         ha='left',
    #         fontsize=8)

if 'latex' in os.environ:
    fig.savefig('experiments/results/depth_statistics.pdf', bbox_inches="tight")
else:
    fig.savefig('experiments/results/depth_statistics.png', bbox_inches="tight")