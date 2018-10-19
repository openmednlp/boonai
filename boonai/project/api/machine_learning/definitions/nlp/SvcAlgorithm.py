from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

from boonai.project.api.machine_learning.definitions.SklearnAlgorithm import \
    SklearnAlgorithm


class SvcAlgorithm(SklearnAlgorithm):
    name = 'NLP SVM'
    description = 'Random Forest for NLP'
    creator = 1  # user id?
    tags = ['nlp', 'text', 'reports']
    groups = ['nlp']

    def train(self, x: List[str], y: List[int]):
        self.pipeline = make_pipeline(
            TfidfVectorizer(),
            LinearSVC()
        )
        self.pipeline.fit(x, y)
