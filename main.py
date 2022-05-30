
import sys
sys.path.insert(0, 'src')
import matplotlib.pyplot as plt
import numpy as np
from graph.dag import DAG
from lib.utils import print_schedule
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default='samples/sample.1.4.json')
# parser.add_argument('--input', '-i', default='samples/sample.3.json')
args = parser.parse_args()

memory_size = 150

dag = DAG()
dag.read_input(args.input)
schedule, makespan, usage = dag.schedule('heft')
print(makespan, usage)
schedule, makespan, usage = dag.schedule('heft_delay', 120)
print(makespan, usage)
###################### LOOKUP VERSION ######################
# try:
schedule, makespan, usage = dag.schedule('heft_lookup', 100, {"depth": 0})
print(makespan, usage)
#     # print_schedule(schedule, makespan, version='lookup')
#     print('Best  Fit:', makespan)
#     schedule, makespan = dag.schedule('heft_lookup', memory_size, {"depth": 1, "strategy": "first"})
#     # print_schedule(schedule, makespan, version='lookup')
#     print('First Fit:', makespan)
# except Exception as e:
#     print(e)
###################### MEMFIRST VERSION ######################
# schedule, makespan, usage = dag.schedule('mem_first', 150)
# print(makespan, usage)
