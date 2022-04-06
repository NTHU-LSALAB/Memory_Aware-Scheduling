from functools import reduce
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graph.edge import Edge


class Node:
    def __init__(self, id: int, cost_table: list[int], output: int, buffer_size: int = 0):
        self.id = id
        self.buffer_size = buffer_size
        self.in_edges: list['Edge'] = []
        self.out_edges: list['Edge'] = []
        self.cost_table = cost_table
        self.cost_avg: float = reduce(
            lambda a, b: a+b, self.cost_table) / len(self.cost_table)
        self.rank: int = None
        self.ast: int = None
        self.aft: int = None
        self.procId: int = None
        self.output = output
        self.round = -1
    
    def rollback(self):
        self.ast = None
        self.aft = None
        self.procId = None

    def __repr__(self):
        return str({
            'buffer_size': self.buffer_size,
            'in_edges': 'empty' if len(self.in_edges) == 0 else self.in_edges,
            'out_edges': 'empty' if len(self.out_edges) == 0 else self.out_edges,
        })
