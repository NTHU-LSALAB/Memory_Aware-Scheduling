import sys
sys.path.insert(0, 'src')

import argparse
from graph.dag import DAG
from lib.utils import print_schedule


parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default='examples/sample.1.json')
args = parser.parse_args()

memory_size = 90

dag = DAG()
dag.read_input(args.input)
schedule, makespan = dag.schedule('heft')
print(makespan)
# print_schedule(schedule, makespan)
###################### DELAY VERSION ######################
# try:
#     schedule, makespan = dag.schedule('heft_delay', memory_size)
#     # print_schedule(schedule, makespan, version='delay')
#     print(makespan)
# except Exception as e:
#     print(e)
###################### LOOKUP VERSION ######################
# schedule, makespan = dag.schedule('heft_lookup', memory_size)
try:
    schedule, makespan = dag.schedule('heft_lookup', memory_size)
    # print_schedule(schedule, makespan, version='lookup')
    print(makespan)
except Exception as e:
    print(e)
