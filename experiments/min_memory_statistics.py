import argparse
import sys

sys.path.insert(0, 'src')
sys.path.insert(0, './')
from converter import converter
from multiprocessing import Pool
import os
import matplotlib.pyplot as plt
from lib.rand_workflow_generator import workflows_generator
from platforms.app import App
import time

processor_list = [2, 3, 5, 7]
task_num_list = [20, 50, 100, 200]
max_out_list = [1, 2, 3, 4, 5]
alpha_list = [0.5, 1.0, 1.5]
beta_list = [0.0, 0.5, 1.0, 2.0]
iterations = 100
method_list = [('heft_dalay', 'delaying', '#3c6f4f'), ('sbac', 'sbac', 'blue'), ('heft_lookup', 'reservation-based', '#edb16d')]

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


def f(app, method, kwargs):
    dag_like, _, _ = workflows_generator(**kwargs)
    dag_like = converter(dag_like)
    app.read_input(dag_like, format='mb')
    _, _, usage = app.schedule('heft')

    return worker(app, method, usage)


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', '-m', default='t')
    args = parser.parse_args()

    name, exp_list = {
        'p': ('processor', processor_list),
        't': ('task_num', task_num_list),
        'm': ('max_out', max_out_list),
        'a': ('alpha', alpha_list),
        'b': ('beta', beta_list)
    }[args.mode]

    app = App()
    columns = []
    for key in exp_list:
        start = time.time()
        print(f'============= {name}: {key} =============')

        min_list = [[] for _ in method_list]
        kwargs = {
            name: key
        }
        # multi-processing
        with Pool() as p:
            for i, method in enumerate(method_list):
                min_list[i] = p.starmap(
                    f, [(app, method[0], kwargs) for _ in range(iterations)])

        columns.append(min_list)
        end = time.time()
        print('time:', format('%.2f' % (end - start)))

    fig = plt.figure(figsize=(8, 6))
    gs = fig.add_gridspec(1, len(columns), hspace=0, wspace=0)
    axs = gs.subplots(sharex='col', sharey='row')
    for i, ax in enumerate(axs):
        bplot = ax.boxplot(columns[i], vert=True,  # vertical box alignment
                           patch_artist=True, boxprops=dict(facecolor=(0, 0, 0, 0)), whiskerprops=dict(linestyle='dashed', linewidth=1.0, color='#333'), medianprops=dict(color='#ff3333'), capprops=dict(color='#333'), widths=.4)
        colors = list(map(lambda method: method[2], method_list))
        idx = 0
        for box, median, flier, color in zip(bplot['boxes'], bplot['medians'], bplot['fliers'], colors):
            box.set_edgecolor(color)
            flier.set_markeredgecolor(color)
            (x_l, y), (x_r, _) = median.get_xydata()

            ax.text(x_l if idx==len(colors)-1 else x_r, y+5,
                    '%d' % y,
                    va='center',
                    ha='right' if idx==len(colors)-1 else'left',
                    fontsize=8)
            idx += 1

        ax.set_xlabel(f'{name} = {exp_list[i]}')
        ax.set_xticks([])
        if i != 0:
            ax.tick_params(left=False)
            ax.spines['left'].set_visible(False)

    fig.legend(bplot['boxes'], list(map(lambda method: method[1], method_list)))

    if 'latex' in os.environ:
        fig.savefig(f'experiments/results/{name}-statistics.eps',
                    format="eps", dpi=1200, bbox_inches="tight", transparent=True)
    else:
        fig.savefig(
            f'experiments/results/{name}-statistics.png', bbox_inches='tight')


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print('total:', format('%.2f' % (end - start)))
