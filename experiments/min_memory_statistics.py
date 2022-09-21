import sys
sys.path.insert(0, 'src')
from platforms.app import App
from lib.real_workflow_generator import dag_generator
from lib.rand_workflow_generator import workflows_generator
import matplotlib.pyplot as plt
import os

num_ranges = [20, 50, 100, 200]
iterations = 20


def worker(method, usage):
    last_memory = mem_size = usage
    while True:
        if mem_size <= 0:
            break

        feasible = False
        for depth in [0] if method == 'heft-delay' else [0, 1, 2]:
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


columns = []
app = App()
for num_range in num_ranges:
    print(f'============= {num_range} =============')

    delay_min_list = []
    lookup_min_list = []
    for i in range(iterations):
        dag_like, _, _ = workflows_generator(task_num=num_range)
        app.read_input(dag_like)
        _, makepan, usage = app.schedule('heft')

        delay_min = worker('heft_delay', usage)
        lookup_min = worker('heft_lookup', usage)
        delay_min_list.append(delay_min)
        lookup_min_list.append(lookup_min)

    columns.append([delay_min_list, lookup_min_list])

fig = plt.figure()
gs = fig.add_gridspec(1, len(columns), hspace=0, wspace=0)
axs = gs.subplots(sharex='col', sharey='row')
for i, ax in enumerate(axs):
    ax.boxplot(columns[i])
    ax.set_xlabel(f'n = {num_ranges[i]}')
    ax.legend(['delaying', 'reservation-based'])
    ax.set_xticks([])

if 'latex' in os.environ:
    fig.savefig('experiments/results/statistics.eps',
                format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig.savefig(
        'experiments/results/statistics.png')
