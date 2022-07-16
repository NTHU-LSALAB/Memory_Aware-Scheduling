import sys
sys.path.insert(0, 'src')
import argparse
from lib.utils import diff, get_parallelism_degree, print_schedule, calculate_idle_time
from platforms.app import App
import numpy as np
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default='samples/sample.1.json')
# parser.add_argument('--input', '-i', default='samples/sample.3.json')
args = parser.parse_args()

memory_size = 200

app = App()
app.read_input(args.input)
schedule, makespan, usage = app.schedule('heft')
print(makespan, usage)
schedule, makespan, usage = app.schedule('cpop')
print(makespan, usage)
schedule, makespan, usage = app.schedule('ippts')
print(makespan, usage)

###################### DELAY VERSION ######################
# schedule, makespan, usage = app.schedule('heft_delay', 200)
# print(makespan, usage, get_parallelism_degree(schedule, makespan))
###################### LOOKUP VERSION ######################
# schedule, makespan, usage = app.schedule('heft_lookup', 300, {"depth": 0})
# print(makespan, usage)
schedule, makespan, usage = app.schedule('heft_lookup', 120, {"depth": 1, 'suffix': '-1'})
print(makespan, usage)
schedule, makespan, usage = app.schedule('cpop_lookup', 120, {"depth": 1, 'suffix': '-1'})
print(makespan, usage)
# schedule, makespan, usage = app.schedule('ippts_lookup', 90, {"depth": 1, 'suffix': '-1'})
# print(makespan, usage)
# schedule2, makespan2, usage2 = app.schedule('heft_lookup', 300, {"depth": 2, 'suffix': '-2'})
# print(makespan2, usage2, get_parallelism_degree(schedule2, makespan2))

###################### MEMFIRST VERSION ######################
# schedule, makespan, usage = dag.schedule('mem_first', 150)
# print(makespan, usage)
