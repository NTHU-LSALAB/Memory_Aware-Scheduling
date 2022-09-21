from functools import reduce
from graph.node import Node

class Task(Node):
    def __init__(self, id: int, cost_table: list[int], output: int, buffer_size: int = 0):
        super().__init__(id)
        self.buffer_size = buffer_size
        self.cost_table = cost_table
        self.cost_avg: float = reduce(
            lambda a, b: a+b, self.cost_table) / len(self.cost_table)
        self.ast: int = None
        self.aft: int = None
        self.procId: int = None
        self.output = output
        self.round = -1
        # ippts
        self.pcm = [None for _ in range(len(cost_table))]
        # cpop
        self.rank_upward: int = None
        self.rank_downward: int = None
        self.is_critical: bool = None
        # graph coloring
        self.buffer_color = None
        self.output_color = None
        self.topics = []
        self.subscribers = []

    def rollback(self):
        self.ast = None
        self.aft = None
        self.procId = None
        self.buffer_color = None
        self.output_color = None
        self.topics = []
        self.subscribers = []

    @property
    def t_out_edges(self):
        return list(filter(lambda edge: not hasattr(edge.target, 'mId'), self.out_edges))

    @property
    def t_in_edges(self):
        return list(filter(lambda edge: not hasattr(edge.source, 'mId'), self.in_edges))

    @property
    def m_out_edges(self):
        return list(filter(lambda edge: hasattr(edge.target, 'mId'), self.out_edges))

    @property
    def m_in_edges(self):
        return list(filter(lambda edge: hasattr(edge.source, 'mId'), self.in_edges))

    def __repr__(self):
        return str({
            'id': self.id,
            'buffer_size': self.buffer_size,
            'in_edges': 'empty' if len(self.in_edges) == 0 else self.in_edges,
            'out_edges': 'empty' if len(self.out_edges) == 0 else self.out_edges,
        }) + '\n'

class MTask(Node):
    def __init__(self, id: int, mId: int, type: str, buffer: int, io_type: str):
        super().__init__(id)
        self.mId = mId
        self.type = type
        self.buffer = buffer
        self.io_type = io_type

    @property
    def t_out_edges(self):
        return list(filter(lambda edge: not hasattr(edge.target, 'mId'), self.out_edges))

    @property
    def t_in_edges(self):
        return list(filter(lambda edge: not hasattr(edge.source, 'mId'), self.in_edges))

    @property
    def m_out_edges(self):
        return list(filter(lambda edge: hasattr(edge.target, 'mId'), self.out_edges))

    @property
    def m_in_edges(self):
        return list(filter(lambda edge: hasattr(edge.source, 'mId'), self.in_edges))

