import sys
sys.path.insert(0, 'src')
import argparse
from lib.utils import diff, get_parallelism_degree, print_schedule, calculate_idle_time
from platforms.app import App
import numpy as np
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser()
# parser.add_argument('--input', '-i', default='samples/sample.1.json')
parser.add_argument('--input', '-i', default='samples/sample.sbac.json')
# parser.add_argument('--input', '-i', default='samples/processor/sample.2.json')
args = parser.parse_args()

memory_size = 200

app = App()
# app.read_input(args.input, weight=False)
app.read_input(args.input, weight=False, format='mb')
schedule, makespan, usage = app.schedule('heft')
print(makespan, usage)
# schedule, makespan, usage = app.schedule('cpop')
# print(makespan, usage)
# # schedule, makespan, usage = app.schedule('ippts')
# # print(makespan, usage)
schedule, makespan, usage = app.schedule('sbac', 60)
print(makespan, usage)

# ###################### DELAY VERSION ######################
# schedule, makespan, usage = app.schedule('heft_delay', 70)
# print(makespan, usage)
# schedule, makespan, usage = app.schedule('cpop_delay', 120)
# print(makespan, usage)
# ###################### LOOKUP VERSION ######################
# schedule, makespan, usage = app.schedule('heft_lookup', 70, {"depth": 0})
# print(makespan, usage)
# schedule, makespan, usage = app.schedule('heft_lookup', 60, {"depth": 1, 'suffix': '-1'})
# print(makespan, usage)
# schedule, makespan, usage = app.schedule('cpop_lookup', 110, {"depth": 1, 'suffix': '-1'})
# print(makespan, usage)
# schedule, makespan, usage = app.schedule('ippts_lookup', 90, {"depth": 1, 'suffix': '-1'})
# print(makespan, usage)
schedule, makespan, usage = app.schedule('heft_lookup', 50, {"depth": 2, 'suffix': '-3'})
print(makespan, usage)

###################### MEMFIRST VERSION ######################
# schedule, makespan, usage = dag.schedule('mem_first', 150)
# print(makespan, usage)
