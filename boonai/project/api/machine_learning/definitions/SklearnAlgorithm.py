from abc import abstractmethod
from typing import List
from sklearn.metrics import roc_curve, auc
from boonai.project.api.machine_learning.definitions.Algorithm import Algorithm


class SklearnAlgorithm(Algorithm):

    @abstractmethod
    def train(self, x, y):
        pass

    def predict(self, x: List[str]):
        if self.pipeline is None:
            self.load()
        return self.pipeline.predict(x)

    def stats(self, y, y_hat):
        fpr, tpr, thresholds = roc_curve(y, y_hat)
        roc_auc = auc(fpr, tpr)
        return roc_auc

    def persist(self):
        self._persist_sklearn()

    def load(self):
        self.pipeline = self._load_sklearn()
