import sys
sys.path.insert(0, 'src')

from platforms.memory import Memory
from graph.dag import DAG

dag = DAG('HEFT')
dag.read_input('examples/sample.2.in')
schedule, makespan = dag.schedule()
print(makespan)
# print('''HEFT SCHEDULE
# ---------------------------
# Proc	Task	AST	AFT
# ---------------------------''')
# for sid, s in enumerate(schedule):
#     for slot in s:
#         print(f'{sid+1}\t{slot["tid"]:<2}\t{slot["AST"]:<2}\t{slot["AFT"]:<2}')
# print(f'''---------------------------
# Makespan = {makespan}
# ---------------------------
# END
# ---------------------------''')

dag = DAG('HEFT_delay')
dag.read_input('examples/sample.2.in')
dag.algo.set_memory(Memory(100))
schedule, makespan = dag.schedule()
print(makespan)
# print('''HEFT_delay SCHEDULE
# ---------------------------
# Proc	Task	AST	AFT
# ---------------------------''')
# for sid, s in enumerate(schedule):
#     for slot in s:
#         print(f'{sid+1}\t{slot["tid"]:<2}\t{slot["AST"]:<2}\t{slot["AFT"]:<2}')
# print(f'''---------------------------
# Makespan = {makespan}
# ---------------------------
# END
# ---------------------------''')
dag = DAG('heft_bf')
dag.read_input('examples/sample.2.in')
dag.algo.set_memory(Memory(110))
schedule, makespan = dag.schedule()
print(makespan)
# print('''BF SCHEDULE
# ---------------------------
# Proc	Task	AST	AFT
# ---------------------------''')
# for sid, s in enumerate(schedule):
#     for slot in s:
#         print(f'{sid+1}\t{slot["tid"]:<2}\t{slot["AST"]:<2}\t{slot["AFT"]:<2}')
# print(f'''---------------------------
# Makespan = {makespan}
# ---------------------------
# END
# ---------------------------''')
