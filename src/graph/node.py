from functools import reduce
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graph.edge import Edge


class Node:
    def __init__(self, id: int):
        self.id = id
        self.in_edges: list['Edge'] = []
        self.out_edges: list['Edge'] = []

    def __repr__(self):
        return str({
            'in_edges': 'empty' if len(self.in_edges) == 0 else self.in_edges,
            'out_edges': 'empty' if len(self.out_edges) == 0 else self.out_edges,
        })
