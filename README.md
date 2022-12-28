# Memory-aware scheduling

## Install

```
pip install matplotlib numpy
python main.py
```

## Usage

```python
from platforms.app import App

app = App()
app.read_input('input_dag.json')

schedule, makespan, usage = app.schedule('heft_lookup', {'depth': 1})
print(makespan, usage)
```

## Experiments

```bash
# influence of different k
python experiments/depth.py
# minimum memory on random dags
python experiments/min_memory_statistics.py
# minimum memory on real world apps
python experiments/min_memory_real.py
# minimal makespan
python experiments/tradeoff.py
```

## Samples

You can find different DAGs under `samples` directory.
- processor: same DAG but different # processors
- width: DAGs with different widths
- size: DAGS with same max width but different # nodes
- dependency: same DAG but different # edges

## Real world applications

You can find real world applications in the paper under `realworld_dax` directory.