import collections
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, './')
import argparse
import numpy as np
from converter import converter
from graph.dag import DAG
from lib.rand_workflow_generator import workflows_generator
from lib.real_workflow_generator import parse_dax, save_dag
import matplotlib.pyplot as plt
import os

parser = argparse.ArgumentParser()
parser.add_argument('--approach', '-a', default='heft')
parser.add_argument('--input', '-i', default='samples/size/sample.15.json')
args = parser.parse_args()

method_list = [('heft_delay', 'delaying', '#00994c', '--o'), ('sbac',
                                                       'sbac', '#004C99', '--^'), ('heft_lookup', 'reservation-based', '#edb16d', '--x')]

def prune_points(data, memories):
    for i, (d, m) in enumerate(zip(data, memories)):
        for dd, mm in zip(data, memories):
            if d > dd and m > mm:
                data[i] = min(data[i], dd)
    return data, memories

def run_experiment():
    fig, ax = plt.subplots(figsize=(12, 6))

    dag = DAG()
    # dag_like = parse_dax('SIGHT', task_num=50)
    # dag_like = converter(dag_like)
    # save_dag(dag_like, '-tradeoff')
    dag.read_input('./experiments/data/tradeoff.json', format='mb')
    _, _, usage = dag.schedule(args.approach)

    def worker(method, usage, marker, label, color):
        mem_size = usage
        mem_data_map = {}
        while True:
            if mem_size <= 0:
                break

            feasible = False
            for depth in [0] if method != 'heft_lookup' else [0, 1, 2]:
                try:
                    _, makepsan, memory = dag.schedule(
                        method, mem_size, {"depth": depth, "plot": False})
                    if makepsan > sys.maxsize/2:
                        continue
                    mem_data_map[memory] = min(makepsan, mem_data_map[memory] if memory in mem_data_map else sys.maxsize)
                    feasible = True
                except Exception:
                    continue
            if not feasible:
                break
            
            mem_size -= 10
        
        mem_data_map = collections.OrderedDict(sorted(mem_data_map.items()))
        data = list(mem_data_map.values())
        memories = list(mem_data_map.keys())
        data, memories = prune_points(data, memories)
        ax.plot(memories, data, marker, label=label, lw=1, color=color,
                dashes=(5, 3), markerfacecolor='none')

    for method in method_list:
        worker(method[0], usage, method[3], method[1], method[2])

    ax.legend(loc="upper right")

    ax.set_xlabel('Memory usage', fontsize=14)
    ax.set_ylabel('Makespan (time unit)', fontsize=14)
    if 'latex' in os.environ:
        fig.savefig(f'experiments/results/{args.approach}_tradeoff.pdf', bbox_inches='tight')
    else:
        fig.savefig(f'experiments/results/{args.approach}_tradeoff.png', bbox_inches='tight')
    plt.close()


run_experiment()
