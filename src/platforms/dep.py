from typing import TYPE_CHECKING

from graph.edge import Edge

if TYPE_CHECKING:
    from platforms.task import Task


class Dep(Edge):
    def __init__(self, source: 'Task', target: 'Task', size: int, weight: int = 0):
        super().__init__(source, target)
        self.size = size
        self.weight = weight

    def __repr__(self):
        return f'{self.source} -> {self.target}: {self.size}'
