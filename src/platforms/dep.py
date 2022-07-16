from typing import TYPE_CHECKING

from graph.edge import Edge

if TYPE_CHECKING:
    from platforms.task import Task


class Dep(Edge):
    def __init__(self, source: 'Task', target: 'Task', size: int, weight: int = 0):
        super().__init__(source, target)
        # buffer size
        self.size = size
        # communication cost
        self.weight = weight

    def __repr__(self):
        return f'{self.source.id} -> {self.target.id}: {self.size}'
