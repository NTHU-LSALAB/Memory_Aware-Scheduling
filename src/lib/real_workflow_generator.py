import json
import random
import time
import sys
from wfcommons.wfchef.recipes import MontageRecipe, GenomeRecipe, EpigenomicsRecipe, SeismologyRecipe
from wfcommons import WorkflowGenerator
import xml.dom.minidom as md

sys.path.insert(0, 'src')
from lib.generator import random_cpu, random_mem

recipe_map = {
    'montage': {
        'name': 'Montage',
        'recipe': MontageRecipe,
        'value': [60, 100, 200]
    },
    'cyber': {
        'name': 'CyberShake',
        'recipe': GenomeRecipe,
        'value': [54, 100, 200]
    },
    'epig': {
        'name': 'Epigenomics',
        'recipe': EpigenomicsRecipe,
        'value': [50, 100, 200]
    },
    'sight': {
        'name': 'Sight',
        'recipe': SeismologyRecipe,
        'value': [103, 150, 200]
    }, 
    'inspiral': {
        'name': 'Inspiral',
        'recipe': SeismologyRecipe,
        'value': [103, 150, 200]
    }
}

def parse_dax(recipe = 'montage', task_num = 50):
    dax = recipe_map[recipe]['name']
    dax = md.parse(f'./realworld_dax/{dax}_{task_num}.xml')
    nodes = dax.getElementsByTagName('job')
    edges = dax.getElementsByTagName('child')
    nodelist = []
    edgelist = []
    node_id_dict = {}
    for i, node in enumerate(nodes):
        id = node.getAttribute('id')
        node_id_dict[id] = i+1
        nodelist.append({
            "id": i+1,
            "costs": [random_cpu(10) for _ in range(3)],
            "output": random_mem(100),
            "buffer": random_mem(100, True)
        })
    for edge in edges:
        parent_list = edge.getElementsByTagName('parent')
        target = edge.getAttribute('ref')
        for parent in parent_list:
            source = parent.getAttribute('ref')
            edgelist.append({
                "source": node_id_dict[source],
                "target": node_id_dict[target],
            })
    return {
        "nodes": nodelist,
        "edges": edgelist,
    }


def dag_generator(recipe = 'montage', task_num = 103):
    random.seed(time.time())
    if task_num < recipe_map[recipe]['value'][0]:
        task_num = recipe_map[recipe]['value'][0]
    generator = WorkflowGenerator(recipe_map[recipe]['recipe'].from_num_tasks(task_num))
    workflow = generator.build_workflow()
    nodelist = []
    edgelist = []
    node_id_dict = {}
    for i, node in enumerate(workflow.nodes):
        node_id_dict[node] = i+1
        nodelist.append({
            "id": i+1,
            "costs": [random_cpu(10) for _ in range(3)],
            "output": random_mem(100),
            "buffer": random_mem(100, True)
        })
    for edge in workflow.edges:
        (source, target) = edge
        edgelist.append({
            "source": node_id_dict[source],
            "target": node_id_dict[target],
        })
    return {
        "nodes": nodelist,
        "edges": edgelist,
    }


def save_dag(dag, affix=''):
    with open(f'real_workflow{affix}.json', 'w') as f:
        json.dump(dag, f, indent=4)
    # workflow.write_json(pathlib.Path('workflow.json'))

def main():
    dag = parse_dax('./realworld_dax/CyberShake_50.xml')
    # dag = dag_generator(task_num=50, recipe='epig')
    save_dag(dag)

if __name__ == '__main__':
    main()