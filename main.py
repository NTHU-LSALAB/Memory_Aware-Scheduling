
from lib.utils import print_schedule
import argparse
import sys
sys.path.insert(0, 'src')
from graph.dag import DAG


parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default='samples/sample.1.json')
args = parser.parse_args()

memory_size = 140

dag = DAG()
dag.read_input(args.input)
schedule, makespan, usage = dag.schedule('heft')
print(makespan, usage)
# processors = [2, 3, 4, 5]
# depths = [0, 1, 2]
# data = [0 for _ in processors]
# for pid, processor in enumerate(processors):
#     dag = DAG()
#     dag.read_input(f'samples/sample.1.{processor}.json')
#     _, _, usage = dag.schedule('heft')
#     min_memory = usage
#     limit = usage
#     min_makespan = sys.maxsize
#     while True:
#         ok = False
#         for depth in depths:
#             # print(usage, limit)
#             try:
#                 _, makespan, memory = dag.schedule(
#                     'heft_lookup', limit, {"depth": depth, "strategy": "best", "plot": False})
#                 min_memory = min(min_memory, memory)
#                 min_makespan = min(min_makespan, makespan)
#                 ok = True
#             except Exception:
#                 pass
#         limit -= 10
#         if not ok:
#             break
#     print(processor, 'processors')
#     print('memory:', min_memory, 'makespan:',
#           min_makespan, 'origin memory:',  usage)
#     data[pid] += (usage - min_memory) / usage
# print(data)
# print_schedule(schedule, makespan)
###################### LOOKUP VERSION ######################
# schedule, makespan = dag.schedule('heft_lookup', memory_size)
# try:
# schedule, makespan, usage = dag.schedule('heft_lookup', memory_size, {"depth": 1, "strategy": "best"})
# print(makespan, usage)
#     # print_schedule(schedule, makespan, version='lookup')
#     print('Best  Fit:', makespan)
#     schedule, makespan = dag.schedule('heft_lookup', memory_size, {"depth": 1, "strategy": "first"})
#     # print_schedule(schedule, makespan, version='lookup')
#     print('First Fit:', makespan)
# except Exception as e:
#     print(e)
###################### MEMFIRST VERSION ######################
# schedule, makespan, usage = dag.schedule('mem_first', memory_size)
# print(makespan, usage)
