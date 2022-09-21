import sys
import time
sys.path.insert(0, 'src')
from platforms.app import App
from lib.rand_workflow_generator import workflows_generator
import matplotlib.pyplot as plt
import numpy as np
import os
from multiprocessing import Pool

num_ranges = [20, 50, 100, 200]
iterations = 20


def worker(app, method, usage):
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

def f(app, method, num_range):
    dag_like, _, _ = workflows_generator(task_num=num_range)
    app.read_input(dag_like)
    _, _, usage = app.schedule('heft')

    return worker(app, method, usage)

def main():
    app = App()
    columns = []
    for num_range in num_ranges:
        print(f'============= {num_range} =============')

        delay_min_list = []
        lookup_min_list = []
        # multi-processing
        # with Pool() as p:
        #     delay_min_list = p.starmap(f, [(app, 'heft_delay', num_range) for _ in range(iterations)])
        #     lookup_min_list = p.starmap(f, [(app, 'heft_lookup', num_range) for _ in range(iterations)])
        # sequential
        for i in range(iterations):
            dag_like, _, _ = workflows_generator(task_num=num_range)
            app.read_input(dag_like)
            _, _, usage = app.schedule('heft')

            delay_min = worker(app, 'heft_delay', usage)
            lookup_min = worker(app, 'heft_lookup', usage)
            delay_min_list.append(delay_min)
            lookup_min_list.append(lookup_min)

        columns.append([delay_min_list, lookup_min_list])

    fig = plt.figure()
    gs = fig.add_gridspec(1, len(columns), hspace=0, wspace=0)
    axs = gs.subplots(sharex='col', sharey='row')
    for i, ax in enumerate(axs):
        bplot = ax.boxplot(columns[i], vert=True,  # vertical box alignment
                        patch_artist=True, boxprops=dict(facecolor=(0, 0, 0, 0)), whiskerprops=dict(linestyle='dashed', linewidth=1.0, color='#333'), medianprops=dict(color='#E58282'), capprops=dict(color='#333'))
        colors = ['#3c6f4f', '#edb16d']
        for box, median, flier, color in zip(bplot['boxes'], bplot['medians'], bplot['fliers'], colors):
            box.set_edgecolor(color)
            flier.set_markeredgecolor(color)
            (x_l, y), (x_r, _) = median.get_xydata()

            ax.text(x_r, y+10,
                    '%d' % y,
                    verticalalignment='center',
                    fontsize=8)

        ax.set_xlabel(f'n = {num_ranges[i]}')
        ax.set_xticks([])

    fig.legend(bplot['boxes'], ['delaying', 'reservation-based'])

    if 'latex' in os.environ:
        fig.savefig('experiments/results/statistics.eps',
                    format="eps", dpi=1200, bbox_inches="tight", transparent=True)
    else:
        fig.savefig(
            'experiments/results/statistics.png')

if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print(end - start)