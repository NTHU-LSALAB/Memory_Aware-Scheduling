import os
import sys
sys.path.insert(0, 'src')
from lib.utils import get_parallelism_degree, get_parallelism_minmax, show_parallelsim_degree
import matplotlib.pyplot as plt
import numpy as np
from platforms.app import App

app = App()
app.read_input('samples/processor/sample.5.json')

depths = [0, 1, 2]
data = [0 for _ in range(len(depths))]
data_minmax = [None for _ in range(len(depths))]
_, _, usage = app.schedule('heft')
print(usage)

# Should we let the memory size constant?
fig, ax = plt.subplots()
for depth, i in enumerate(depths):
    schedule, makespan, usage = app.schedule(
        'heft_lookup', 160, {"depth": depth})
    data[i] = get_parallelism_degree(schedule, makespan)
    data_minmax[i] = get_parallelism_minmax(schedule, makespan)
    degree = show_parallelsim_degree(schedule, makespan)
    X = np.arange(makespan)
    ax.step(X, degree)
    print(makespan, usage, data[i])
ax.set_yticks(np.arange(len(schedule)) + 1)
ax.legend(depths)

_fig, _ax = plt.subplots()
_X = np.arange(len(depths))
mins = list(map(lambda minmax: minmax[0], data_minmax))
maxs = list(map(lambda minmax: minmax[1], data_minmax))
# _ax.plot(_X, data)
_ax.vlines(_X, mins, maxs)
_ax.set_yticks(np.arange(5) + 1)
_ax.set_xticks(_X)
_fig.savefig('experiments/results/_depth.png')

if 'latex' in os.environ:
    fig.savefig('experiments/results/depth.eps', format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig.savefig('experiments/results/depth.png')
