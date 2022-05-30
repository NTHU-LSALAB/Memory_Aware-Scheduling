
import sys
sys.path.insert(0, 'src')
import matplotlib.pyplot as plt
import numpy as np
from graph.dag import DAG

processors = [2, 3, 4, 5]
depths = [0, 1, 2]
data = [[0 for _ in processors] for _ in range(3)]
data_exec = [[0 for _ in processors] for _ in range(3)]
for pid, processor in enumerate(processors):
    print('======processor ' + str(processor) + '=======')
    dag = DAG()
    dag.read_input(f'samples/sample.1.{processor}.json')
    _, origin_makespan, usage = dag.schedule('heft')
    min_memory = min_memory2 = usage
    min_memory_makespan = min_memory_makespan2 = origin_makespan
    # limit = usage
    min_makespan = min_makespan2 = sys.maxsize
    memory_sizes = [usage - 5*i for i in range(40)]
    for limit in memory_sizes:
        for depth in depths:
            try:
                _, makespan, memory = dag.schedule(
                    'heft_lookup', limit, {"depth": depth, "plot": False})
                if makespan > 1000:
                    continue
                if memory < min_memory:
                    min_memory = memory
                    min_memory_makespan = makespan
                min_makespan = min(min_makespan, makespan)
            except Exception:
                pass
    print('delay')
    for limit in memory_sizes:
        try:
            _, makespan, memory = dag.schedule('heft_delay', limit, {"plot": False})
            if makespan > 1000:
                continue
            if memory < min_memory2:
                min_memory2 = memory
                min_memory_makespan2 = makespan
            min_makespan2 = min(min_makespan2, makespan)
        except Exception as e:
            pass
    # print(processor, 'processors')
    print('memory:', min_memory, 'makespan:',
          min_memory_makespan, 'origin memory:',  usage)
    data[0][pid] = min_memory
    data[1][pid] = min_memory2
    data[2][pid] = usage

    data_exec[0][pid] = min_memory_makespan
    data_exec[1][pid] = min_memory_makespan2
    data_exec[2][pid] = origin_makespan

X = np.arange(len(processors))
fig, ax = plt.subplots()
rects = ax.bar(X + 0.00, data[0], color='#FF7F0C', width=0.25)
rects2 = ax.bar(X + 0.25, data[1], color='g', width=0.25)
ax.bar(X + 0.5, data[2], color='#1F77B4', width=0.25)
def autolabel(rects):
    for i, rect in enumerate(rects):
        h = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., h+5, '%.2f%%'%(100*(h- data[2][i])/data[2][i]),
                ha='center', va='bottom')
autolabel(rects)
autolabel(rects2)
ax.set_xticks(X, labels=['2', '3', '4', '5'])
ax.legend(labels=['heft-lookup', 'heft-delay', 'heft'])
ax.set_title("Minimal memory usage")
ax.set_xlabel('# processors')
ax.set_ylabel('Usage')
fig.savefig('exp.png')

fig_exec, ax_exec = plt.subplots()
rects = ax_exec.bar(X + 0.00, data_exec[0], color='#FF7F0C', width=0.25)
rects2 = ax_exec.bar(X + 0.25, data_exec[1], color='g', width=0.25)
ax_exec.bar(X + 0.5, data_exec[2], color='#1F77B4', width=0.25)
def autolabel_exec(rects):
    for i, rect in enumerate(rects):
        h = rect.get_height()
        ax_exec.text(rect.get_x()+rect.get_width()/2., h+5, '%.2f%%'%(100*(h- data_exec[2][i])/data_exec[2][i]),
                ha='center', va='bottom')
autolabel_exec(rects)
autolabel(rects2)
ax_exec.set_xticks(X, labels=['2', '3', '4', '5'])
ax_exec.legend(labels=['heft-lookup', 'heft-delay', 'heft'])
ax_exec.set_title("Increased makespan")
ax_exec.set_xlabel('# processors')
ax_exec.set_ylabel('Makespan')
fig_exec.savefig('exp_exec.png')


