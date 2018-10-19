from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

from boonai.project.api.machine_learning.definitions.SklearnAlgorithm import \
    SklearnAlgorithm


class GridSearchSvcAlgorithm(SklearnAlgorithm):
    name = 'NLP Grid Search SVM'
    description = 'Random Forest for NLP'
    creator = 1  # user id?
    tags = ['nlp', 'text', 'reports']
    groups = ['nlp']
    pipeline = None

    def train(self, x: List[str], y: List[int]):
        pipeline = make_pipeline(
            TfidfVectorizer(),
            LinearSVC()
        )
        parameters = {
            'tfidfvectorizer__use_idf': (True, False),
            'linearsvc__C': [1, 10, 100]
        }

        self.pipeline = GridSearchCV(pipeline, cv=3, n_jobs=4, param_grid=parameters)
        self.pipeline.fit(x, y)
