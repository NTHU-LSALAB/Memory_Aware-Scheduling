from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graph.node import Node


class Edge:
    def __init__(self, source: 'Node', target: 'Node', size: int, weight: int = 0):
        self.source = source
        self.target = target
        self.size = size
        self.weight = weight

    def __repr__(self):
        return f'{self.source} -> {self.target}: {self.weight}'
