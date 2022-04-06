import sys
sys.path.insert(0, 'src')

from graph.dag import DAG

# dag = DAG()
# dag.read_input('examples/sample.2.in')
# schedule, makespan = dag.schedule('heft')
# print(makespan)
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

dag = DAG()
dag.read_input('examples/sample.3.json')
schedule, makespan = dag.schedule('heft')
print(makespan)
try:
    schedule, makespan = dag.schedule('heft_delay', 100)
    print(makespan)
except Exception as e:
    print(e)
    pass
try:
    schedule, makespan = dag.schedule('heft_lookup', 90)
    print(makespan)
except Exception as e:
    print(e)
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
# dag = DAG()
# dag.read_input('examples/sample.3.in')
# dag.algo.set_memory(Memory(90))
# schedule, makespan = dag.schedule('heft_bf')
# print(makespan)
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
