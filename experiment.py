import sys

from yaml import parse
sys.path.insert(0, 'src')
import uuid
from lib.generator import plot_DAG, workflows_generator
from graph.dag import DAG
import os
import json
from openpyxl import Workbook
import argparse

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
            _, makespan, usage = dag.schedule('heft')
            log.write(f'HEFT ORIGIN: {makespan}, MEMEORY: {usage}\n')
            ws.append(['ORIGIN', makespan, usage])
            log.write(f'================= HEFT LOOKUP =================\n')
            memory_sizes = [usage - 10*i for i in range(20)]
            ws.append(['Depth/Memory']+memory_sizes)
            for depth in depths:
                depth_row = [depth]
                for memory_size in memory_sizes:
                    log.write(f'DEPTH: {depth} MEMORY: {memory_size}\n')
                    try:
                        _, makespan = dag.schedule(
                            'heft_lookup', memory_size, {"depth": depth, "strategy": args.strategy})
                        log.write(f'{makespan}\n')
                        depth_row.append(makespan)
                    except Exception as e:
                        depth_row.append('N/A')
                        error_log.write(f'{e}\n')
                ws.append(depth_row)

        for graph in range(num_of_graph):
            worker(graph)
        wb.save(f'{folder}/result.xlsx')


generate_graph()
run_experiment()
