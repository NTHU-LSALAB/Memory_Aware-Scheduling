import argparse
import json
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, './')
from converter import converter
from multiprocessing import Pool
import os
import matplotlib.pyplot as plt
from lib.rand_workflow_generator import workflows_generator
from lib.real_workflow_generator import save_dag
from platforms.app import App
import time

processor_list = [2, 3, 5, 7]
task_num_list = [20, 50, 100, 200]
# max_out_list = [1, 2, 3, 4, 5]
max_out_list = [1, 2, 3, 4]
alpha_list = [0.5, 1.0, 1.5]
beta_list = [0.0, 0.5, 1.0, 2.0]
iterations = 100
methods = [('', 'baseline', 'black'), ('delay', 'delaying', '#00994c'), ('sbac', 'sbac', '#004C99'), ('lookup', 'reservation-based', '#edb16d')]


def worker(app, method, usage):
    last_memory = mem_size = usage
    while True:
        if mem_size <= 0:
            break

        feasible = False
        for depth in [0] if 'lookup' not in method else [0, 1, 2]:
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


def f(i, app, method, kwargs, algorithm = 'heft'):
    # dag_like = workflows_generator(**kwargs)
    # dag_like = converter(dag_like)
    filename = '-'.join(list(map(lambda item: item[0] + '-' + str(item[1]),kwargs.items()))) + '-' + str(i)
    # save_dag(dag_like, f'./experiments/data/rand/{filename}.json')
    app.read_input(f'./experiments/data/rand/{filename}.json', format='mb')
    _, _, usage = app.schedule(algorithm)
    if method == algorithm:
        return usage

    return worker(app, method, usage)


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', '-m', default='t')
    parser.add_argument('--algorithm', '-a', default='heft')
    args = parser.parse_args()

    method_list = list(map(lambda method: (args.algorithm if method[0] == '' else args.algorithm+'_'+method[0], *method[1:]), methods))

    name, exp_list = {
        'p': ('processor', processor_list),
        't': ('task_num', task_num_list),
        'm': ('max_out', max_out_list),
        'a': ('alpha', alpha_list),
        'b': ('beta', beta_list)
    }[args.mode]

    skip = False
    if os.path.exists(f'./experiments/results/{args.algorithm}-{name}-statistics.json'):
        skip = True

    if not skip:
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
                        f, [(iter, app, method[0], kwargs, args.algorithm) for iter in range(iterations)])

            columns.append(min_list)
            end = time.time()
            print('time:', format('%.2f' % (end - start)))
        with open(f'./experiments/results/{args.algorithm}-{name}-statistics.json', 'w') as file:
            json.dump({
                "columns": columns,
            }, file, indent=4)
    else:
        with open(f'./experiments/results/{args.algorithm}-{name}-statistics.json', 'r') as file:
            result = json.load(file)
            columns = result['columns']

    fig = plt.figure(figsize=(8, 3.5 if args.algorithm == 'cpop' else 6))
    gs = fig.add_gridspec(1, len(columns), hspace=0, wspace=0)
    axs = gs.subplots(sharex='col', sharey='row')
    for i, ax in enumerate(axs):
        ax.set_zorder(10 - i)
        bplot = ax.boxplot(columns[i], vert=True, showfliers=False,
                           patch_artist=True, boxprops=dict(facecolor=(0, 0, 0, 0)), whiskerprops=dict(linestyle='dashed', linewidth=1.0, color='#333'), medianprops=dict(color='#ff3333'), capprops=dict(color='#333'), widths=.4 if args.algorithm == 'cpop' else .4)
        colors = list(map(lambda method: method[2], method_list))
        idx = 0
        for box, median, color in zip(bplot['boxes'], bplot['medians'], colors):
            box.set_edgecolor(color)
            # (x_l, y), (x_r, _) = median.get_xydata()

            # ax.text(x_l if idx==len(colors)-1 else x_r, y+5,
            #         '%d' % y,
            #         va='center',
            #         ha='right' if idx==len(colors)-1 else'left',
            #         fontsize=8)
            idx += 1

        ax.set_xlabel(f'{name} = {exp_list[i]}', fontsize=12)
        ax.set_xticks([])
        if i == 0:
            ax.set_ylabel('Minimum memory', fontsize=14)
            ax.legend(bplot['boxes'], list(map(lambda method: method[1], method_list)), loc='upper left', fontsize=10)
        else:
            ax.tick_params(left=False)
            ax.spines['left'].set_visible(False)

    # fig.supxlabel(' ', fontsize=14)
    if 'latex' in os.environ:
        fig.savefig(
            f'experiments/results/{args.algorithm}-{name}-statistics.pdf', bbox_inches='tight')
    else:
        fig.savefig(
            f'experiments/results/{args.algorithm}-{name}-statistics.png', bbox_inches='tight')


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print('total:', format('%.2f' % (end - start)))
