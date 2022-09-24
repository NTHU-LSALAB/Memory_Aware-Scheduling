from copy import deepcopy
import json
from os import listdir
from os.path import isfile, join
import random
import math
import argparse
import numpy as np
from matplotlib import pyplot as plt
import networkx as nx
from networkx.readwrite import json_graph
plt.switch_backend('Agg')

set_dag_size = [10, 20, 30, 40, 50]  # random number of DAG  nodes
set_max_out = [1, 2, 3, 4, 5]  # max out_degree of one node
set_alpha = [0.5, 1.0, 1.5]  # DAG shape
set_beta = [0.0, 0.5, 1.0, 2.0]  # DAG regularity


def DAGs_generate(n=10, max_out=2, alpha=1, beta=1.0):

    length = math.floor(math.sqrt(n)/alpha)
    mean_value = n/length
    random_num = np.random.normal(
        loc=mean_value, scale=beta,  size=(length, 1))
    ###############################################division#############################################
    position = {'Start': (0, 4), 'Exit': (10, 4)}
    generate_num = 0
    dag_num = 1
    dag_list = []
    for i in range(len(random_num)):
        dag_list.append([])
        for j in range(math.ceil(random_num[i])):
            dag_list[i].append(j)
        generate_num += len(dag_list[i])

    if generate_num != n:
        if generate_num < n:
            for i in range(n-generate_num):
                index = random.randrange(0, length, 1)
                dag_list[index].append(len(dag_list[index]))
        if generate_num > n:
            i = 0
            while i < generate_num-n:
                index = random.randrange(0, length, 1)
                if len(dag_list[index]) <= 1:
                    continue
                else:
                    del dag_list[index][-1]
                    i += 1

    dag_list_update = []
    pos = 1
    max_pos = 0
    for i in range(length):
        dag_list_update.append(list(range(dag_num, dag_num+len(dag_list[i]))))
        dag_num += len(dag_list_update[i])
        pos = 1
        for j in dag_list_update[i]:
            position[j] = (3*(i+1), pos)
            pos += 5
        max_pos = pos if pos > max_pos else max_pos
        position['Start'] = (0, max_pos/2)
        position['Exit'] = (3*(length+1), max_pos/2)

    ############################################link#####################################################
    into_degree = [0]*n
    out_degree = [0]*n
    edges = []
    pred = 0

    for i in range(length-1):
        sample_list = list(range(len(dag_list_update[i+1])))
        for j in range(len(dag_list_update[i])):
            od = random.randrange(1, max_out+1, 1)
            od = len(dag_list_update[i+1]
                     ) if len(dag_list_update[i+1]) < od else od
            bridge = random.sample(sample_list, od)
            for k in bridge:
                edges.append((dag_list_update[i][j], dag_list_update[i+1][k]))
                into_degree[pred+len(dag_list_update[i])+k] += 1
                out_degree[pred+j] += 1
        pred += len(dag_list_update[i])

    ######################################create start node and exit node################################
    for node, id in enumerate(into_degree):
        if id == 0:
            edges.append(('Start', node+1))
            into_degree[node] += 1

    for node, od in enumerate(out_degree):
        if od == 0:
            edges.append((node+1, 'Exit'))
            out_degree[node] += 1

    return edges, position


def plot_DAG(edges, postion, filename):
    g1 = nx.DiGraph()
    g1.add_edges_from(edges)
    nx.draw_networkx(g1, arrows=True, pos=postion)
    plt.savefig(filename, format="PNG")
    plt.close()


def build_graph(edges):
    g1 = nx.DiGraph()
    g1.add_edges_from(edges)
    return json_graph.node_link_data(g1)


def random_cpu(t):
    # if random.random() < args.prob if hasattr(args, 'prob') else 1:
    #     return random.sample(range(1, 3 * t), 1)[0]
    # else:
    return random.sample(range(5 * t, 10 * t), 1)[0]


def random_mem(r, is_buffer=False):
    if is_buffer:
        return round(random.uniform(0.03 * r, 0.1 * r))
    else:
        return round(random.uniform(0.05 * r, 0.5 * r))


def workflows_generator(task_num=20, max_out=2, alpha=1, beta=1.0, processor=3, t_unit=10, resource_unit=100):
    t = t_unit  # s   time unit
    r = resource_unit  # resource unit
    edges, pos = DAGs_generate(task_num, max_out, alpha, beta)

    dag = build_graph(edges)

    def transform(obj, key):
        if obj[key] == 'Start':
            obj[key] = 1
        elif obj[key] == 'Exit':
            obj[key] = len(dag['nodes'])
        else:
            obj[key] = obj[key] + 1

    for node in dag['nodes']:
        transform(node, 'id')
        node['costs'] = [random_cpu(t) for _ in range(processor)]
        node['output'] = random_mem(r)
        node['buffer'] = random_mem(r, True)

    for link in dag['links']:
        transform(link, 'source')
        transform(link, 'target')

    dag['input'] = random_mem(r)
    dag['edges'] = dag['links']
    del dag['links']

    return dag, edges, pos


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default='default',
                        type=str)  # parameters setting
    parser.add_argument('--n', default=10, type=int)  # number of DAG  nodes
    # max out_degree of one node
    parser.add_argument('--max_out', default=4, type=float)
    parser.add_argument('--alpha', default=1, type=float)  # shape
    parser.add_argument('--beta', default=1.0, type=float)  # regularity
    parser.add_argument('--out')
    parser.add_argument('--processor', default=3)
    args = parser.parse_args()
    ##############################################initialize############################################
    if args.mode == 'random':
        args.n = random.sample(set_dag_size, 1)[0]
        args.max_out = random.sample(set_max_out, 1)[0]
        args.alpha = random.sample(set_alpha, 1)[0]
        args.beta = random.sample(set_alpha, 1)[0]
        args.prob = 0.8
    else:
        args.prob = 1

    dag, edges, pos = workflows_generator(args.n, args.max_out, args.alpha, args.beta, args.processor)
    new_filename = args.out
    if not new_filename:
        onlyfiles = [f for f in listdir(
            'samples') if isfile(join('samples', f))]
        latest = int(
            max(list(map(lambda file: int(file.split('.')[1]), onlyfiles))))
        new_filename = f'sample.{latest+1}'

    plot_DAG(edges, pos, 'out/dag/'+new_filename+'.png')
    with open('samples/'+new_filename+'.json', 'w') as f:
        json.dump(dag, f, indent=4)
