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
    dag.read_input('./samples/sample.1.4.json')
    _, makespan_origin, usage = dag.schedule('heft')
    memory_sizes = [usage - 5*i for i in range(40)]

    def worker(method):
        data = []
        for depth in depths:
            depth_row = [depth]
            for memory_size in memory_sizes:
                if memory_size <= 0:
                    continue
                try:
                    _, makespan, _ = dag.schedule(
                        method, memory_size, {"depth": depth, "plot": False})
                    depth_row.append(makespan)
                    print(makespan, memory_size)
                except Exception:
                    depth_row.append('N/A')
            data.append(depth_row[1:])
        data = np.array(data)
        data = data.T.tolist()
        data = list(map(lambda mems:
                        min(list(map(lambda mem: sys.maxsize if mem == 'N/A' else int(mem), mems))), data))

        x = []
        y = []
        for i, data in enumerate(data):
            if data > 1000:
                continue
            x.append((data - makespan_origin) / makespan_origin)
            y.append((-10*i) / usage)

        print(x, y)

        color = "#"+''.join([random.choice('0123456789ABCDEF')
                            for _ in range(6)])
        ax.plot(x, y, '--o', color=color, label=method)

    worker('heft_lookup')
    worker('mem_first')

    # for graph in range(num_of_graph):
    #     worker(graph)
    # wb.save(f'{folder}/result.xlsx')
    ax.set_title("Memory-Makespan")
    ax.set_xlabel('Increased Makespan')
    ax.set_ylabel('Reduced Memory')
    # ax.set_ylim(-1, 0)
    fig.savefig('exp.png')
    plt.close()


# generate_graph()
run_experiment()
