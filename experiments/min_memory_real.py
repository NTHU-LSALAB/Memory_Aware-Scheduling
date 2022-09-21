import os
import sys
sys.path.insert(0, 'src')
import matplotlib.pyplot as plt
from lib.rand_workflow_generator import workflows_generator
from lib.real_workflow_generator import dag_generator, save_dag
from platforms.app import App

num_ranges = [50, 100, 200]

def worker(method, usage):
    last_memory = mem_size = usage
    while True:
        if mem_size <= 0:
            break

        feasible = False
        for depth in [0] if method == 'heft-delay' else [0, 1, 2]:
            try:
                _, makepsan, memory = app.schedule(
                    method, mem_size, {"depth": depth, "plot": False})
                last_memory = memory
                if makepsan > sys.maxsize/2:
                    continue
                feasible = True
            except Exception:
                continue
        if not feasible:
            return last_memory
        mem_size -= 10

recipes = ['montage', 'genome', 'epig']
xticks = []
app = App()
delay_data = []
lookup_data = []
for recipe in recipes:
    for num_range in num_ranges:
        print(f'============= {num_range} =============')

        dag_like, _, _ = workflows_generator(task_num=num_range)
        save_dag(dag_like, f'-{recipe}-{num_range}')
        app.read_input(dag_like)
        _, makepan, usage = app.schedule('heft')

        delay_min = worker('heft_delay', usage)
        lookup_min = worker('heft_lookup', usage)

        delay_data.append(delay_min)
        lookup_data.append(lookup_min)
        xticks.append(f'{recipe[:4]}.-{num_range}')

fig, ax= plt.subplots()
ax.plot(xticks, delay_data, '--x', color='#3c6f4f')
ax.plot(xticks, lookup_data, '--o', color='#edb16d')
ax.legend(['delaying', 'reservation-based'])
plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')

if 'latex' in os.environ:
    fig.savefig('experiments/results/real.eps',
                format="eps", dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig.savefig(
        'experiments/results/real.png')
