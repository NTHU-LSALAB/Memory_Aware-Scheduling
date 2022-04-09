import sys
sys.path.insert(0, 'src')

import argparse
from graph.dag import DAG
from lib.utils import print_schedule


parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default='samples/sample.1.json')
args = parser.parse_args()

memory_size = 130

dag = DAG()
dag.read_input(args.input)
schedule, makespan, usage = dag.schedule('heft')
print(makespan, usage)
# print_schedule(schedule, makespan)
###################### LOOKUP VERSION ######################
# schedule, makespan = dag.schedule('heft_lookup', memory_size)
try:
    schedule, makespan = dag.schedule('heft_lookup', memory_size, {"depth": 1, "strategy": "best"})
    # print_schedule(schedule, makespan, version='lookup')
    print('Best  Fit:', makespan)
    schedule, makespan = dag.schedule('heft_lookup', memory_size, {"depth": 1, "strategy": "first"})
    # print_schedule(schedule, makespan, version='lookup')
    print('First Fit:', makespan)
except Exception as e:
    print(e)
