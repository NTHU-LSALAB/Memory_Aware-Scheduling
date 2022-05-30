import sys
sys.path.insert(0, 'src')

import matplotlib
import matplotlib.pyplot as plt
from graph.dag import DAG
import numpy as np
import random

# matplotlib.use('pdf')
# matplotlib.rcParams.update({
#     "pgf.texsystem": "pdflatex",
#     'font.family': 'serif',
#     'text.usetex': True,
#     'pgf.rcfonts': False,
# })

depths = [0, 1, 2]


def run_experiment():
    fig, ax = plt.subplots()

    dag = DAG()
    dag.read_input('./samples/sample.1.3.json')
    _, makespan_origin, usage = dag.schedule('heft')
    memory_sizes = [usage - 5*i for i in range(40)]

    def worker(method):
        data = []
        memorys = []
        for depth in depths:
            depth_row = [depth]
            for memory_size in memory_sizes:
                if memory_size <= 0:
                    memorys.append(memory_size)
                    depth_row.append('N/A')
                    continue
                try:
                    _, makespan, memory = dag.schedule(
                        method, memory_size, {"depth": depth, "plot": False})
                    depth_row.append(makespan)
                    memorys.append(memory)
                except Exception:
                    memorys.append(memory_size)
                    depth_row.append('N/A')
            data.append(depth_row[1:])
        data = np.array(data)
        data = data.T.tolist()
        data = list(map(lambda mems:
                        min(list(map(lambda mem: sys.maxsize if mem == 'N/A' else int(mem), mems))), data))

        def remove_bad_points(data):
            x = []
            y = []
            for i, makespan in enumerate(data):
                if makespan > 1000:
                    continue
                x.append((makespan - makespan_origin) / makespan_origin)
                y.append((memorys[i] - usage) / usage)

            remove_indices = []
            for i, (t, m) in enumerate(zip(x, y)):
                for xx, yy in zip(x, y):
                    if t >= xx and m > yy:
                        remove_indices.append(i)
            x = [i for j, i in enumerate(x) if j not in remove_indices]
            y = [i for j, i in enumerate(y) if j not in remove_indices]
            return x, y
        
        x, y = remove_bad_points(data)

        color = "#"+''.join([random.choice('0123456789ABCDEF')
                            for _ in range(6)])
        ax.plot(x, y, '--o', color=color, label=method)

    worker('heft_lookup')
    worker('heft_delay')
    ax.legend(loc="upper right")

    # for graph in range(num_of_graph):
    #     worker(graph)
    # wb.save(f'{folder}/result.xlsx')
    ax.set_title("Memory-Makespan")
    ax.set_xlabel('Increased Makespan')
    ax.set_ylabel('Reduced Memory')
    # ax.set_ylim(-1, 0)
    fig.savefig('tradeoff.png')
    plt.close()


# generate_graph()
run_experiment()
