from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVC

from boonai.project.api.machine_learning.definitions.SklearnAlgorithm import \
    SklearnAlgorithm


class SvmProbaAlgorithm(SklearnAlgorithm):
    name = 'NLP Grid Search SVM Proba'
    description = 'Grid Search SVM Proba'
    creator = 1  # user id?
    tags = ['nlp', 'text', 'reports', 'svm', 'svc', 'proba']
    groups = ['nlp', 'svm', 'grid-search']
    pipeline = None

    def train(self, x: List[str], y: List[int]):
        pipeline = make_pipeline(
            TfidfVectorizer(),
            SVC(probability=True)
        )
        parameters = {
            'tfidfvectorizer__use_idf': (True, False),
            'svc__C': [0.1, 0.5, 1, 2, 5, 10, 20, 50, 100],
            'svc__random_state': [42],
            'svc__kernel': ['linear', 'rbf', 'poly']
        }

        self.pipeline = GridSearchCV(pipeline, cv=3, n_jobs=4, param_grid=parameters)
        self.pipeline.fit(x, y)
        print(self.pipeline.best_params_)

    def predict(self, x: List[str]):
        if self.pipeline is None:
            self.load()
        return self.pipeline.predict_proba(x)
