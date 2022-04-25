import sys
sys.path.insert(0, 'src')

import matplotlib
import matplotlib.pyplot as plt
import argparse
from openpyxl import Workbook
import json
import os
from graph.dag import DAG
from lib.generator import plot_DAG, workflows_generator
import uuid
import numpy as np
import random
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
num_of_graph = 10
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


def generate_graph():
    print(f'Generating {num_of_graph} graphs...')

    def worker(graph):
        dag, edges, pos = workflows_generator(mode=args.mode)
        plot_DAG(edges, pos, f'{folder}/dags/dag.{graph}.png')
        with open(f'{folder}/samples/exp.'+str(graph)+'.json', 'w') as f:
            json.dump(dag, f, indent=4)
        print(f'Graph {graph:>2}... Done')

    for graph in range(num_of_graph):
        worker(graph)


def run_experiment():
    fig, ax = plt.subplots()
    with open(f'{folder}/log/result.log', 'w') as log, open(f'{folder}/log/error.log', 'w') as error_log:
        wb = Workbook()
        ws = wb.active
        ws.title = f'{num_of_graph} Random Graphs'
        ws.column_dimensions['A'].width = 15

        def worker(graph):
            print(f'Run graph {graph}...')
            ws.append([f'Graph {graph}'])
            log.write(f'================ Graph {graph} ================\n')
            dag = DAG()
            dag.read_input(f'{folder}/samples/exp.'+str(graph)+'.json')
            _, makespan_origin, usage = dag.schedule('heft')
            log.write(f'HEFT ORIGIN: {makespan_origin}, MEMEORY: {usage}\n')
            ws.append(['ORIGIN', makespan_origin, usage])
            log.write(f'================= HEFT LOOKUP =================\n')
            memory_sizes = [usage - 10*i for i in range(20)]
            ws.append(['Depth/Memory']+memory_sizes)

            data = []
            for depth in depths:
                depth_row = [depth]
                for memory_size in memory_sizes:
                    log.write(f'DEPTH: {depth} MEMORY: {memory_size}\n')
                    try:
                        _, makespan = dag.schedule(
                            'heft_lookup', memory_size, {"depth": depth, "strategy": args.strategy, "plot": False})
                        log.write(f'{makespan}\n')
                        depth_row.append(makespan)
                    except Exception as e:
                        depth_row.append('N/A')
                        error_log.write(f'{e}\n')
                data.append(depth_row[1:])
                ws.append(depth_row)
            data = np.array(data)
            data = data.T.tolist()
            data = list(map(lambda mems:
                            min(list(map(lambda mem: sys.maxsize if mem == 'N/A' else int(mem), mems))), data))

            x = []
            y = []
            for i, data in enumerate(data):
                if data > 1000:
                    continue
                x.append((data - makespan_origin) / makespan_origin)
                y.append((-10*i) / usage)

            color = "#"+''.join([random.choice('0123456789ABCDEF')
                                for _ in range(6)])
            ax.plot(x, y, '--o', color=color)

        for graph in range(num_of_graph):
            worker(graph)
        wb.save(f'{folder}/result.xlsx')
    ax.set_title("Memory-Makespan")
    ax.set_xlabel('Increased Makespan')
    ax.set_ylabel('Reduced Memory')
    # ax.set_ylim(-1, 0)
    fig.savefig(f'{folder}/exp.png')
    plt.close()


generate_graph()
run_experiment()
