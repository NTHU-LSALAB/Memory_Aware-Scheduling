from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graph.node import Node


class Edge:
    def __init__(self, source: 'Node', target: 'Node'):
        self.source = source
        self.target = target

    def __repr__(self):
        return f'{self.source.id} -> {self.target.id}'
