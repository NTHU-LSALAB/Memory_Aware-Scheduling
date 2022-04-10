import sys
sys.path.insert(0, 'src')
import random
import numpy as np
import uuid
from lib.generator import plot_DAG, workflows_generator
from graph.dag import DAG
import os
import json
from openpyxl import Workbook
import argparse
import matplotlib.pyplot as plt
import matplotlib
import copy

# matplotlib.use('pdf')
# matplotlib.rcParams.update({
#     "pgf.texsystem": "pdflatex",
#     'font.family': 'serif',
#     'text.usetex': True,
#     'pgf.rcfonts': False,
# })
parser = argparse.ArgumentParser()
parser.add_argument('--mode', '-m', default='random')
parser.add_argument('--strategy', '-s', default='best')
args = parser.parse_args()


# Generate 100 graphs
num_of_graph = 1
depths = [0, 1, 2]

random_id = str(uuid.uuid4())[:8]
folder = f'{args.mode}.{num_of_graph}.{args.strategy}.{random_id}'

if not os.path.exists(folder):
    os.mkdir(folder)
if not os.path.exists(f'{folder}/samples'):
    os.mkdir(f'{folder}/samples')
if not os.path.exists(f'{folder}/dags'):
    os.mkdir(f'{folder}/dags')
if not os.path.exists(f'{folder}/log'):
    os.mkdir(f'{folder}/log')

processors = [2, 3, 4, 5, 6, 7, 8]


def generate_graph():
    print(f'Generating {num_of_graph} graphs...')

    def worker(graph, processor):
        dag, edges, pos = workflows_generator(
            mode=args.mode, processor=processor)
        plot_DAG(edges, pos, f'{folder}/dags/dag.{graph}.png')
        # with open(f'{folder}/samples/exp.'+str(graph)+'.json', 'w') as f:
        #     json.dump(dag, f, indent=4)
        with open(f'{folder}/samples/exp.{graph}.{processor}.json', 'w') as f:
            json.dump(dag, f, indent=4)
        # print(f'Graph {graph:>2}... Done')

    for graph in range(num_of_graph):
        for processor in processors:
            worker(graph, processor)


def run_experiment():
    fig, ax = plt.subplots()
    # with open(f'{folder}/log/result.log', 'w') as log, open(f'{folder}/log/error.log', 'w') as error_log:
    #     wb = Workbook()
    #     ws = wb.active
    #     ws.title = f'{num_of_graph} Random Graphs'
    #     ws.column_dimensions['A'].width = 15

    data = [0 for _ in processors]

    def worker(graph, processor, pid):
        print(f'Run with {processor} processors...')
        # ws.append([f'Graph {graph}'])
        # log.write(f'================ Graph {graph} ================\n')
        dag = DAG()
        dag.read_input(f'{folder}/samples/exp.{graph}.{processor}.json')
        _, _, usage = dag.schedule('heft')
        # _, makespan_origin, usage = dag.schedule('heft')
        # log.write(f'HEFT ORIGIN: {makespan_origin}, MEMEORY: {usage}\n')
        # ws.append(['ORIGIN', makespan_origin, usage])
        # log.write(f'================= HEFT LOOKUP =================\n')
        # memory_sizes = [usage - 10*i for i in range(20)]
        # ws.append(['Depth/Memory']+memory_sizes)

        # data = []
        # for depth in depths:
        #     depth_row = [depth]
        #     for memory_size in memory_sizes:
        #         log.write(f'DEPTH: {depth} MEMORY: {memory_size}\n')
        #         try:
        #             _, makespan = dag.schedule(
        #                 'heft_lookup', memory_size, {"depth": depth, "strategy": args.strategy, "plot": False})
        #             log.write(f'{makespan}\n')
        #             depth_row.append(makespan)
        #         except Exception as e:
        #             depth_row.append('N/A')
        #             error_log.write(f'{e}\n')
        #     data.append(depth_row[1:])
        #     ws.append(depth_row)
        # data = np.array(data)
        # data = data.T.tolist()
        # data = list(map(lambda mems:
        #                 min(list(map(lambda mem: sys.maxsize if mem == 'N/A' else int(mem), mems))), data))

        # x = []
        # y = []
        # for i, data in enumerate(data):
        #     if data > 1000:
        #         continue
        #     x.append((data - makespan_origin) / makespan_origin)
        #     y.append((-10*i) / usage)

        # remove_indices = []
        # for i, (t, m) in enumerate(zip(x, y)):
        #     for xx, yy in zip(x, y):
        #         if t >= xx and m > yy:
        #             remove_indices.append(i)
        # x = [i for j, i in enumerate(x) if j not in remove_indices]
        # y = [i for j, i in enumerate(y) if j not in remove_indices]

        # color = "#"+''.join([random.choice('0123456789ABCDEF')
        #                     for _ in range(6)])
        # ax.plot(x, y, '--o', color=color, label=f'{graph}')
        # ax.legend()
        min_memory = usage
        limit = usage
        while True:
            ok = False
            for depth in depths:
                # print(usage, limit)
                try:
                    _, _, memory = dag.schedule(
                        'heft_lookup', limit, {"depth": depth, "strategy": args.strategy, "plot": False})
                    min_memory = min(min_memory, memory)
                    ok = True
                except Exception:
                    pass
            limit -= 10
            if not ok:
                break
        # print(min_memory, usage)
        data[pid] += (usage - min_memory) / usage
        # ax.bar(id, min_memory, color='b', width=0.25, label='lookup')
        # ax.bar(id+0.25, usage, color='g', width=0.25, label='heft')

    for graph in range(num_of_graph):
        for pid, processor in enumerate(processors):
            worker(graph, processor, pid)

    print(list(map(lambda d: d/num_of_graph, data)))
    ax.bar(processors, data, label='Memeory reduction')
    ax.legend()
    # wb.save(f'{folder}/result.xlsx')
    # ax.set_title("Memory-Makespan")
    # ax.set_xlabel('Increased Makespan')
    # ax.set_ylabel('Reduced Memory')
    ax.set_title("Memory-Processor")
    ax.set_xlabel('# Processors')
    ax.set_ylabel('Memory Usage')
    # ax.set_ylim(-1, 0)
    fig.savefig(f'{folder}/exp.png')
    plt.close()


generate_graph()
run_experiment()
