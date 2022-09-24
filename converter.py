import sys
sys.path.insert(0, 'src')
import json
import matplotlib.pyplot as plt
from graph.dag import DAG

def converter(dag_obj, format='default'):
    nodelist = []
    edgelist = []
    if isinstance(dag_obj, dict):
        dag_obj = DAG(dag_obj)
    for node in dag_obj.tasks:
        nodelist.append({
            "id": node.id,
            "costs": node.cost_table,
            "buffer": node.buffer_size,
            "output": node.output
        })

    for edge in dag_obj.edges:
        edgelist.append({
            "source": edge.source.id,
            "target": edge.target.id,
        })
    # create mem task
    m_tasks = []
    pk = len(dag_obj.tasks) + 1
    m_tasks.append({
        "id": pk,
        "mId": 1,
        "buffer": dag_obj.input,
        "type": "allocate",
        "io_type": "input"
    })
    edgelist.append({
        "source": pk,
        "target": 1
    })
    pk += 1
    m_tasks.append({
        "id": pk,
        "mId": 1,
        "type": "free",
        "io_type": "input"
    })
    edgelist.append({
        "source": 1,
        "target": pk
    })
    pk += 1
    for node in dag_obj.tasks:
        node_id = node.id
        buffer = node.buffer_size
        output = node.output
        # internal buffer mTask
        # allocate
        m_tasks.append({
            "id": pk,
            "mId": node_id,
            "buffer": buffer,
            "type": "allocate",
            "io_type": "buffer"
        })
        edgelist.append({
            "source": pk,
            "target": node_id,
        })
        pk += 1
        # free
        m_tasks.append({
            "id": pk,
            "mId": node_id,
            "type": "free",
            "io_type": "buffer"
        })
        edgelist.append({
            "source": node_id,
            "target": pk,
        })
        pk += 1
        # output buffer mTask
        # allocate
        m_tasks.append({
            "id": pk,
            "mId": node_id,
            "buffer": output,
            "type": "allocate",
            "io_type": "output"
        })
        edgelist.append({
            "source": pk,
            "target": node_id,
        })
        pk += 1
        # free
        for out_edge in node.out_edges:
            child = out_edge.target.id
            edgelist.append({
                "source": child,
                "target": pk
            })
        m_tasks.append({
            "id": pk,
            "mId": node_id,
            "type": "free",
            "io_type": "output"
        })
        pk += 1

    return {
        "nodes": nodelist,
        "edges": edgelist,
        "mTasks": m_tasks
    }

def main():
    plt.figure(figsize=(3.8, 4), dpi=1000)
    dag = DAG()
    dag.read_input('samples/sample.3.json')

    dag_like = converter(dag, 'default')    

    with open('samples/mb/sample.3.json', 'w') as f:
        json.dump(dag_like, f, indent=4)


if __name__ == '__main__':
    main()
