from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from graph.edge import Edge


class Node:
    def __init__(self, id: int):
        self.id = id
        self.in_edges: list['Edge'] = []
        self.out_edges: list['Edge'] = []
        self.priority: int = None

    def __repr__(self):
        return str({
            'in_edges': 'empty' if len(self.in_edges) == 0 else self.in_edges,
            'out_edges': 'empty' if len(self.out_edges) == 0 else self.out_edges,
        })
        
    def is_entry(self):
        return len(self.in_edges) == 0

    def is_exit(self):
        return len(self.out_edges) == 0

    def __lt__(self, other):
        return self.priority > other.priority

    def __eq__(self, other):
        return self.id == other.id