from abc import abstractmethod
from typing import List

from boonai.project.api.machine_learning.definitions.Algorithm import Algorithm


class SklearnAlgorithm(Algorithm):
    @abstractmethod
    def train(self, x, y):
        pass

    def predict(self, x: List[str]):
        if self.pipeline is None:
            self.load()
        return self.pipeline.predict(x)

    def persist(self):
        self._persist_sklearn()

    def load(self):
        self.pipeline = self._load_sklearn()
