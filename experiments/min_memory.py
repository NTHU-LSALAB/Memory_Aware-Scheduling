import sys
sys.path.insert(0, 'src')
import argparse
from graph.dag import DAG
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os

parser = argparse.ArgumentParser()
parser.add_argument('--mode', '-m', default='p')
parser.add_argument('--approach', '-a', default='heft')
args = parser.parse_args()

widths = [3, 4, 5, 7]
dependencies = [13, 15, 18, 20]
sizes = [7, 10, 15, 22]
processors = [2, 3, 4, 5]
depths = [0, 1, 2]

name, exp_list = {
    'p': ('processor', processors),
    'w': ('width', widths),
    'd': ('dependency', dependencies),
    's': ('size', sizes)
}[args.mode]


data = [[0 for _ in exp_list] for _ in range(3)]
data_exec = [[0 for _ in exp_list] for _ in range(3)]
for id, exp in enumerate(exp_list):
    print('======' + name + ' ' + str(exp) + '=======')
    dag = DAG()
    dag.read_input(f'samples/{name}/sample.{exp}.json', weight=False)
    _, origin_makespan, usage = dag.schedule(args.approach)
    min_memory = min_memory2 = usage
    min_memory_makespan = min_memory_makespan2 = origin_makespan
    # limit = usage
    min_makespan = min_makespan2 = sys.maxsize
    memory_sizes = [usage - 5*i for i in range(40)]
    for limit in memory_sizes:
        for depth in depths:
            try:
                _, makespan, memory = dag.schedule(
                    f'{args.approach}_reserve', limit, {"depth": depth, "plot": False})
                if makespan > 1000:
                    continue
                if memory < min_memory:
                    min_memory = memory
                    min_memory_makespan = makespan
                min_makespan = min(min_makespan, makespan)
            except Exception:
                pass
    for limit in memory_sizes:
        try:
            _, makespan, memory = dag.schedule(
                f'{args.approach}_delay', limit, {"plot": False})
            if makespan > 1000:
                continue
            if memory < min_memory2:
                min_memory2 = memory
                min_memory_makespan2 = makespan
            min_makespan2 = min(min_makespan2, makespan)
        except Exception as e:
            pass

    print(f'Original Memory: {usage}, Original Makespan: {origin_makespan}')
    print(f'{args.approach} reserve:', min_memory,  min_memory_makespan)
    print(f'{args.approach} delay:', min_memory2,  min_memory_makespan2)
    data[0][id] = min_memory
    data[1][id] = min_memory2
    data[2][id] = usage

    # print(min_memory*min_makespan, min_memory2*min_makespan2)

    data_exec[0][id] = min_memory_makespan
    data_exec[1][id] = min_memory_makespan2
    data_exec[2][id] = origin_makespan

X = np.arange(len(processors))
fig, ax = plt.subplots()
ax.grid(axis='y')
ax.set_axisbelow(True)
rects = ax.bar(X + 0.00, data[0], color='#edb16d', alpha=0.9, width=0.25)
rects2 = ax.bar(X + 0.26, data[1], color='#00994c', alpha=0.9, width=0.25)
ax.bar(X + 0.52, data[2], color='#1f57a4', alpha=0.9, width=0.25)


def autolabel(rects):
    for i, rect in enumerate(rects):
        h = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., h+5, '%.0f%%' % (100*(h - data[2][i])/data[2][i]),
                ha='center', va='bottom', size=8)


autolabel(rects)
autolabel(rects2)
ax.set_ylim([0, max(data[:][2])*1.75])
ax.set_xticks(X + 0.26, labels=exp_list)
ax.legend(labels=['reservation-based', 'delaying', 'original'])
# ax.set_title("Minimal memory usage")
ax.set_xlabel(f'# {name.capitalize()}', fontsize=20)
ax.set_ylabel('Memory Usage', fontsize=20)
for spine in ax.spines.values():
    spine.set_edgecolor('grey')
if 'latex' in os.environ:
    # ax.set_rasterized(True)
    fig.savefig(f'experiments/results/{args.approach}_{name}_memory.eps',
                format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig.savefig(f'experiments/results/{args.approach}_{name}_memory.png')


fig_exec, ax_exec = plt.subplots()
ax_exec.grid(axis='y')
ax_exec.set_axisbelow(True)
rects = ax_exec.bar(X + 0.00, data_exec[0], fc='white', ec='#edb16d', hatch='xx', width=0.25)
rects2 = ax_exec.bar(X + 0.28, data_exec[1], fc='white', ec='#00994c', hatch='xx', width=0.25)
ax_exec.bar(X + 0.524, data_exec[2], fc='white', ec='#1f57a4', hatch='xx', width=0.25)


def autolabel_exec(rects):
    for i, rect in enumerate(rects):
        h = rect.get_height()
        ax_exec.text(rect.get_x()+rect.get_width()/2., h+5, '%.0f%%' % (100*(h - data_exec[2][i])/data_exec[2][i]),
                     ha='center', va='bottom', size=8)


autolabel_exec(rects)
autolabel_exec(rects2)
ax_exec.set_ylim([0, max(data[:][0])*1.75])
ax_exec.set_xticks(X + 0.28, labels=exp_list)
ax_exec.legend(labels=['reservation-based', 'delaying', 'original'])
# ax_exec.set_title("Increased makespan")
ax_exec.set_xlabel(f'# {name.capitalize()}', fontsize=20)
ax_exec.set_ylabel('Makespan', fontsize=20)
for spine in ax_exec.spines.values():
    spine.set_edgecolor('grey')
if 'latex' in os.environ:
    # ax_exec.set_rasterized(True)
    fig_exec.savefig(f'experiments/results/{args.approach}_{name}_makespan.eps',
                     format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig_exec.savefig(
        f'experiments/results/{args.approach}_{name}_makespan.png')
