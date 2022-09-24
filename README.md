# Heterogeneous scheduling with memory constraints

## Usage

```
pip install matplotlib numpy networkx
python main.py
```

## Experiments

```
python experiments/min_memory.py
python experiments/tradeoff.py
python experiments/depth.py
```

## Samples

You can find different DAGs under `samples` directory.
- processor: same DAG but different # processors
- width: DAGs with different widths
- size: DAGS with same max width but different # nodes
- dependency: same DAG but different # edges