import sys
sys.path.insert(0, 'src')

import csv
from lib.generator import plot_DAG, workflows_generator
from graph.dag import DAG
import os
import json
from openpyxl import Workbook


if not os.path.exists('tmp'):
    os.mkdir('tmp')
if not os.path.exists('tmp/samples'):
    os.mkdir('tmp/samples')
if not os.path.exists('tmp/dags'):
    os.mkdir('tmp/dags')
if not os.path.exists('tmp/log'):
    os.mkdir('tmp/log')
################### Fittable Experiment ###################
# HEFT w/o constraints
# HEFT delay
# HEFT lookup with different depths

# Generate 100 graphs
num_of_graph = 100
depths = [0, 1, 2]

with open('tmp/log/result.log', 'w') as log, open('tmp/log/error.log', 'w') as error_log:
    wb = Workbook()
    ws = wb.active
    ws.title = '100 Random Graphs'
    ws.column_dimensions['A'].width = 15
    for graph in range(num_of_graph):
        ws.append([f'Graph {graph}'])
        log.write(f'================ Graph {graph} ================\n')
        dag = DAG()
        dag.read_input('tmp/samples/exp.'+str(graph)+'.json')
        schedule, makespan, usage = dag.schedule('heft')
        log.write(f'HEFT ORIGIN: {makespan}, MEMEORY: {usage}\n')
        ws.append(['ORIGIN', makespan, usage])
        log.write(f'================= HEFT LOOKUP =================\n')
        memory_sizes = [usage - 10*i for i in range(10)]
        ws.append(['Depth/Memory']+memory_sizes)
        for depth in depths:
            depth_row = [depth]
            for memory_size in memory_sizes:
                log.write(f'DEPTH: {depth} MEMORY: {memory_size}\n')
                try:
                    schedule, makespan = dag.schedule(
                        'heft_lookup', memory_size, {"depth": depth})
                    log.write(f'{makespan}\n')
                    depth_row.append(makespan)
                except Exception as e:
                    depth_row.append('N/A')
                    error_log.write(f'{e}\n')
            ws.append(depth_row)
    wb.save('tmp/result.xlsx')
# for graph in range(num_of_graph):
#     dag, edges, pos = workflows_generator()
#     plot_DAG(edges, pos, 'tmp/dags/dag.'+str(graph)+'.png')
#     with open('tmp/samples/exp.'+str(graph)+'.json', 'w') as f:
#         json.dump(dag, f, indent=4)

################### Trade-off Experiment ###################
# HEFT w/o constraints
# HEFT lookup with different depths


# os.rmdir('tmp')
