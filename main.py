
import sys
sys.path.insert(0, 'src')

from graph.dag import DAG


def print_schedule(schedule, makespan, version=''):
    print(f'''HEFT {version} SCHEDULE
---------------------------
Proc	Task	AST	AFT
---------------------------''')
    for sid, s in enumerate(schedule):
        for slot in s:
            print(f'{sid+1}\t{slot.id:<2}\t{slot.ast:<2}\t{slot.aft:<2}')
    print(f'''---------------------------
Makespan = {makespan}
---------------------------
END
---------------------------''')


memory_size = 160

dag = DAG()
dag.read_input('examples/sample.1.json')
# schedule, makespan = dag.schedule('heft')
# print(makespan)
# print_schedule(schedule, makespan)
# try:
#     schedule, makespan = dag.schedule('heft_delay', memory_size)
#     # print_schedule(schedule, makespan, version='delay')
#     # print(makespan)
# except Exception as e:
#     print(e)
schedule, makespan = dag.schedule('heft_lookup', memory_size)
# try:
#     schedule, makespan = dag.schedule('heft_lookup', memory_size)
#     # print_schedule(schedule, makespan, version='lookup')
#     print(makespan)
# except Exception as e:
#     print(e)
