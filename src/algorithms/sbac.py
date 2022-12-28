from functools import reduce
import numpy as np
from platforms.task import Task


def adjust_priority(tasks: list[Task]):
    for task in tasks:
        if len(task.m_out_edges) > 0 and task.id != 0:  # releaser
            releaser = task
            release_mIds = list(
                map(lambda edge: edge.target.mId, task.m_out_edges))
            releaser_pairs = []
            for p_task in tasks:
                # pair need to be consumer
                for edge in p_task.m_in_edges:
                    if edge.source.mId in release_mIds:
                        releaser_pairs.append(p_task)

            vc_list = []
            for adj_edge in releaser.t_in_edges:  # adj
                if len(adj_edge.source.m_in_edges) > 0:  # consumer
                    consumer = adj_edge.source
                    consume_mIds = list(
                        map(lambda edge: edge.source.mId, consumer.m_in_edges))
                    consumer_pairs = []
                    for p_task in tasks:
                        # pair need to be releaser
                        for edge in p_task.m_out_edges:
                            if edge.target.mId in consume_mIds:
                                consumer_pairs.append(p_task)
                    if consumer.priority < np.average(list(map(lambda pair: pair.priority, releaser_pairs))):
                        vc_list.append(consumer)
                        continue
                    isnot_adj = True
                    for c_pair in consumer_pairs:
                        for r_pair in releaser_pairs:
                            if r_pair in list(map(lambda edge: edge.target, c_pair.t_out_edges)):
                                isnot_adj = False
                    if isnot_adj:
                        vc_list.append(consumer)
            for adj_edge in releaser.t_out_edges:  # adj
                if len(adj_edge.target.m_in_edges) > 0:  # consumer
                    consumer = adj_edge.source
                    consume_mIds = list(
                        map(lambda edge: edge.source.mId, consumer.m_in_edges))
                    consumer_pairs = []
                    for p_task in tasks:
                        # pair need to be releaser
                        for edge in p_task.m_out_edges:
                            if edge.target.mId in consume_mIds:
                                consumer_pairs.append(p_task)
                    if consumer.priority < np.average(list(map(lambda pair: pair.priority, releaser_pairs))):
                        vc_list.append(consumer)
                        continue
                    isnot_adj = True
                    for c_pair in consumer_pairs:
                        for r_pair in releaser_pairs:
                            if r_pair in list(map(lambda edge: edge.target, c_pair.t_out_edges)):
                                isnot_adj = False
                    if isnot_adj:
                        vc_list.append(consumer)
            releaser.priority += reduce(lambda prev,
                                        curr: prev + curr.priority, vc_list, 0)
