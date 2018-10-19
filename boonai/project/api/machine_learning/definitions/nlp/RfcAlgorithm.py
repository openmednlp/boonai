from typing import List

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline

from boonai.project.api.machine_learning.definitions.SklearnAlgorithm import \
    SklearnAlgorithm


class RfcAlgorithm(SklearnAlgorithm):
    name = 'NLP RFC'
    description = 'Random Forest for NLP'
    creator = 1  # user id?
    tags = ['nlp', 'text', 'reports']
    groups = ['nlp']

    def train(self, x: List[str], y: List[int]):
        # Accepts list of texts as
        self.pipeline = make_pipeline(
            TfidfVectorizer(),
            RandomForestClassifier()
        )
        self.pipeline.fit(x, y)
