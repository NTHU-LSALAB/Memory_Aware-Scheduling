from graph.dag import DAG
from platforms.memory import Memory


class App(DAG):
    def __init__(self) -> None:
        super().__init__()

        self.algo: Memory = None
