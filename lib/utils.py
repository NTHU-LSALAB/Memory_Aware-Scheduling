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
