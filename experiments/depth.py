import os
import sys
sys.path.insert(0, 'src')
from lib.utils import get_parallelism_degree, get_parallelism_minmax, show_parallelsim_degree
import matplotlib.pyplot as plt
import numpy as np
from platforms.app import App

app = App()
app.read_input('samples/width/sample.5.json', weight=False)

depths = [0, 1, 2, 3, 4]
data = [0 for _ in range(len(depths))]
data_minmax = [None for _ in range(len(depths))]
data_makespan = [0 for _ in range(len(depths))]
_, _, original_usage = app.schedule('heft')

# Should we let the memory size constant?
fig, ax = plt.subplots()
for depth, i in enumerate(depths):
    schedule, makespan, usage = app.schedule(
        'heft_lookup', original_usage, {"depth": depth})
    data_makespan[i] = makespan
    data[i] = get_parallelism_degree(schedule, makespan)
    data_minmax[i] = get_parallelism_minmax(schedule, makespan)
    degree = show_parallelsim_degree(schedule, makespan)
    X = np.arange(makespan)
    ax.step(X, degree)
    print(depth, makespan, usage, data[i])
ax.set_yticks(np.arange(len(schedule)) + 1)
ax.legend(depths)

_fig, _ax = plt.subplots()
_X = np.arange(len(depths))
_ax.plot(_X, data)
# mins = list(map(lambda minmax: minmax[0], data_minmax))
# maxs = list(map(lambda minmax: minmax[1], data_minmax))
# # _ax.plot(_X, data)
# _ax.vlines(_X, mins, maxs)
data.insert(0, 1.5)
_ax.set_yticks(list(map(lambda d: float(format(d, '.2f')), (data))))
_ax.set_xticks(_X)
_ax.set_xlabel('Depth k', fontsize=20)
_ax.set_ylabel('Degree of parallelism', fontsize=20)


fig_makespan, ax_makespan = plt.subplots()
ax_makespan.plot(_X, data_makespan)
# ax_makespan.set_yticks(list(map(lambda d: d, data_makespan)))
ax_makespan.set_xticks(_X)
ax_makespan.set_xlabel('Depth k', fontsize=20)
ax_makespan.set_ylabel('Makespan', fontsize=20)

if 'latex' in os.environ:
    _fig.savefig('experiments/results/depth_parallel.eps', format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    _fig.savefig('experiments/results/depth_parallel.png')

if 'latex' in os.environ:
    fig.savefig('experiments/results/depth.eps', format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig.savefig('experiments/results/depth.png')

if 'latex' in os.environ:
    fig_makespan.savefig('experiments/results/depth_makespan.eps', format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig_makespan.savefig('experiments/results/depth_makespan.png')
