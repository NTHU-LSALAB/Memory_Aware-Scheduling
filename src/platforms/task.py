from functools import reduce
from typing import TYPE_CHECKING

from graph.node import Node

if TYPE_CHECKING:
    from platforms.dep import Dep


class Task(Node):
    def __init__(self, id: int, cost_table: list[int], output: int, buffer_size: int = 0):
        super().__init__(id)
        self.buffer_size = buffer_size
        self.cost_table = cost_table
        self.cost_avg: float = reduce(
            lambda a, b: a+b, self.cost_table) / len(self.cost_table)
        self.priority: int = None
        self.ast: int = None
        self.aft: int = None
        self.procId: int = None
        self.output = output
        self.round = -1
        # graph coloring
        self.buffer_color = None
        self.output_color = None
        self.subscribers = []

    def rollback(self):
        self.ast = None
        self.aft = None
        self.procId = None
        self.buffer_color = None
        self.output_color = None
        self.subscribers = []

    def is_entry(self):
        return len(self.in_edges) == 0

    def is_exit(self):
        return len(self.out_edges) == 0

    def __repr__(self):
        return str({
            'buffer_size': self.buffer_size,
            'in_edges': 'empty' if len(self.in_edges) == 0 else self.in_edges,
            'out_edges': 'empty' if len(self.out_edges) == 0 else self.out_edges,
        })
