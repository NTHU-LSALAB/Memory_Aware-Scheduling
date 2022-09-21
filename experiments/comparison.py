import sys
sys.path.insert(0, 'src')
from platforms.app import App
import numpy as np
import matplotlib.pyplot as plt
import os

app = App()
app.read_input('samples/sample.sbac.json', weight=False, format='mb')

methods = ['heft_lookup', 'heft_lookup', 'heft_lookup', 'heft_delay', 'sbac', 'heft']
labels = ['reservation-based(2)', 'reservation-based(1)', 'reservation-based(0)', 'delaying', 'sbac', 'original']
slots = [5, 6, 7, 8, 9]
data = [[0 for _ in slots] for _ in range(len(methods))]

fig, ax = plt.subplots()
for i, slot in enumerate(slots):
    for j, method in enumerate(methods):
        try:
            schedule, makespan, usage = app.schedule(
                method, slot * 10, {"depth": 2-j})
            data[j][i] = makespan
        except Exception as e:
            # print(e)
            data[j][i] = 0

X = np.arange(len(slots))
colors = ['red', 'blue', 'green', 'grey', 'orange']
for i in range(len(methods)):
    if methods[i] == 'heft':
        ax.bar(X + 0.1*i, data[i], color='black', width=0.1)
    else:
        ax.bar(X + 0.1*i, data[i], fc='white', ec=colors[i], width=0.1, hatch='x')
ax.set_xticks(X+0.2, labels=slots)
ax.set_ylim([0, max(data[:][0])*1.75])
ax.set_xlabel('Number of memory slots', fontsize=20)
ax.set_ylabel('Makespan', fontsize=20)
ax.legend(labels)

if 'latex' in os.environ:
    fig.savefig('experiments/results/comparison.eps', format="eps",
                dpi=1200, bbox_inches="tight", transparent=True)
else:
    fig.savefig('experiments/results/comparison.png')
