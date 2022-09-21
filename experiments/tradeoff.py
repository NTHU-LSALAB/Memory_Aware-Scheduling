import sys
sys.path.insert(0, 'src')
import argparse
import random
import numpy as np
from graph.dag import DAG
import matplotlib.pyplot as plt
import matplotlib
import os

parser = argparse.ArgumentParser()
parser.add_argument('--approach', '-a', default='heft')
parser.add_argument('--input', '-i', default='rand_workflow.json')
args = parser.parse_args()

depths = [0, 1, 2]


def run_experiment():
    fig, ax = plt.subplots()

    dag = DAG()
    # dag.read_input('samples/size/sample.15.json', weight=False)
    dag.read_input(args.input, weight=False)
    # dag.read_input('samples/mb/sample.2.json', weight=False, format='mb')
    _, makespan_origin, usage = dag.schedule(args.approach)
    memory_sizes = [usage - 10*i for i in range(100)]
    print(usage)

    def worker(method, marker, label):
        data = []
        memorys = []
        for depth in depths:
            depth_row = [depth]
            for memory_size in memory_sizes:
                # print(memory_size)
                if memory_size <= 0:
                    memorys.append(memory_size)
                    depth_row.append('N/A')
                    continue
                try:
                    _, makespan, memory = dag.schedule(
                        method, memory_size, {"depth": depth, "plot": False})
                    # print(makespan, memory)
                    depth_row.append(makespan)
                    memorys.append(memory)
                    # print(memory)
                except Exception:
                    memorys.append(memory_size)
                    # print('N/A')
                    depth_row.append('N/A')
            data.append(depth_row[1:])
        data = np.array(data)
        data = data.T.tolist()
        data = list(map(lambda mems:
                        min(list(map(lambda mem: sys.maxsize if mem == 'N/A' else int(mem), mems))), data))
        def remove_bad_points(data):
            x = []
            y = []
            for i, makespan in enumerate(data):
                if makespan > sys.maxsize/2:
                    continue
                x.append(makespan)
                y.append(memorys[i])

            remove_indices = []
            for i, (t, m) in enumerate(zip(x, y)):
                for xx, yy in zip(x, y):
                    if t >= xx and m > yy:
                        remove_indices.append(i)
            x = [i for j, i in enumerate(x) if j not in remove_indices]
            y = [i for j, i in enumerate(y) if j not in remove_indices]
            return x, y

        x, y = remove_bad_points(data)
        ax.plot(y, x, marker, label=label, lw=1, color='#333333',
                dashes=(5, 3), markerfacecolor='none')

    worker(f'{args.approach}_lookup', '--o', 'reservation-based')
    worker(f'{args.approach}_delay', '--x', 'delaying')
    # worker(f'sbac', '--^', 'sbac')
    ax.legend(loc="upper right")

    # for graph in range(num_of_graph):
    #     worker(graph)
    # wb.save(f'{folder}/result.xlsx')
    # ax.set_title("Memory-Makespan")
    ax.set_xlabel('Memory Usage', fontsize=20)
    ax.set_ylabel('Makespan', fontsize=20)
    # ax.set_ylim(-1, 0)
    if 'latex' in os.environ:
        fig.savefig(f'experiments/results/{args.approach}_tradeoff.eps',
                    format="eps", dpi=1200, bbox_inches="tight", transparent=True)
    else:
        fig.savefig(f'experiments/results/{args.approach}_tradeoff.png')
    plt.close()


# generate_graph()
run_experiment()
