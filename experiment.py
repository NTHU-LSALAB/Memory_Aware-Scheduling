import sys
sys.path.insert(0, 'src')

import random
import numpy as np
import uuid
from lib.generator import plot_DAG, workflows_generator
import os
import json
from openpyxl import Workbook
import argparse
import matplotlib.pyplot as plt
import matplotlib
import copy
from graph.dag import DAG

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
folder = f'processor.{args.mode}.{num_of_graph}.{args.strategy}.{random_id}'

if not os.path.exists(folder):
    os.mkdir(folder)
if not os.path.exists(f'{folder}/samples'):
    os.mkdir(f'{folder}/samples')
if not os.path.exists(f'{folder}/dags'):
    os.mkdir(f'{folder}/dags')
if not os.path.exists(f'{folder}/log'):
    os.mkdir(f'{folder}/log')

processors = [2, 3, 4, 5, 6, 7]


def generate_graph():
    print(f'Generating {num_of_graph} graphs...')

    def worker(graph, processor):
        dag, edges, pos = workflows_generator(
            mode=args.mode, processor=processor, max_out=1, alpha=0.5, beta=0.5, n=40)
        plot_DAG(edges, pos, f'{folder}/dags/dag.{graph}.{processor}.png')
        with open(f'{folder}/samples/exp.{graph}.{processor}.json', 'w') as f:
            json.dump(dag, f, indent=4)

    for graph in range(num_of_graph):
        for processor in processors:
            worker(graph, processor)


def run_experiment():
    fig, ax = plt.subplots()

    data = [0 for _ in processors]

    def worker(graph, processor, pid):
        print(f'Run with {processor} processors...')
        dag = DAG()
        dag.read_input(f'{folder}/samples/exp.{graph}.{processor}.json')
        _, _, usage = dag.schedule('heft')
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
    ax.set_title("Memory-Processor")
    ax.set_xlabel('# Processors')
    ax.set_ylabel('Memory Usage')
    fig.savefig(f'{folder}/exp.png')
    plt.close()


generate_graph()
run_experiment()
