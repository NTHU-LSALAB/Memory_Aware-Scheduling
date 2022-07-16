
import os
import sys
sys.path.insert(0, 'src')
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from graph.dag import DAG
import argparse

# matplotlib.use('pdf')
# matplotlib.rcParams.update({
#     "pgf.texsystem": "pdflatex",
#     'font.family': 'serif',
#     'text.usetex': True,
#     'pgf.rcfonts': False,
# })

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
                    f'{args.approach}_lookup', limit, {"depth": depth, "plot": False})
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
            _, makespan, memory = dag.schedule(f'{args.approach}_delay', limit, {"plot": False})
            if makespan > 1000:
                continue
            if memory < min_memory2:
                min_memory2 = memory
                min_memory_makespan2 = makespan
            min_makespan2 = min(min_makespan2, makespan)
        except Exception as e:
            pass

    print(f'Original Memory: {usage}, Original Makespan: {origin_makespan}')
    print(f'{args.approach} lookup:', min_memory,  min_memory_makespan)
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
rects = ax.bar(X + 0.00, data[0], color='#FF7F0C', width=0.25)
rects2 = ax.bar(X + 0.25, data[1], color='g', width=0.25)
ax.bar(X + 0.5, data[2], color='#1F77B4', width=0.25)
def autolabel(rects):
    for i, rect in enumerate(rects):
        h = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., h+5, '%.2f%%'%(100*(h- data[2][i])/data[2][i]),
                ha='center', va='bottom')
autolabel(rects)
autolabel(rects2)
ax.set_xticks(X, labels=exp_list)
ax.legend(labels=[f'{args.approach}-lookup', f'{args.approach}-delay', f'{args.approach}'])
# ax.set_title("Minimal memory usage")
ax.set_xlabel(f'# {name}')
ax.set_ylabel('Usage')
if 'latex' in os.environ:
    fig.savefig(f'experiments/results/{args.approach}_{name}_memory.eps', format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig.savefig(f'experiments/results/{args.approach}_{name}_memory.png')


fig_exec, ax_exec = plt.subplots()
rects = ax_exec.bar(X + 0.00, data_exec[0], color='#FF7F0C', width=0.25)
rects2 = ax_exec.bar(X + 0.25, data_exec[1], color='g', width=0.25)
ax_exec.bar(X + 0.5, data_exec[2], color='#1F77B4', width=0.25)
def autolabel_exec(rects):
    for i, rect in enumerate(rects):
        h = rect.get_height()
        ax_exec.text(rect.get_x()+rect.get_width()/2., h+5, '%.2f%%'%(100*(h- data_exec[2][i])/data_exec[2][i]),
                ha='center', va='bottom')
autolabel_exec(rects)
autolabel(rects2)
ax_exec.set_xticks(X, labels=exp_list)
ax_exec.legend(labels=[f'{args.approach}-lookup', f'{args.approach}-delay', f'{args.approach}'])
# ax_exec.set_title("Increased makespan")
ax_exec.set_xlabel(f'# {name}')
ax_exec.set_ylabel('Makespan')
if 'latex' in os.environ:
    fig_exec.savefig(f'experiments/results/{args.approach}_{name}_makespan.eps', format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig_exec.savefig(f'experiments/results/{args.approach}_{name}_makespan.png')


