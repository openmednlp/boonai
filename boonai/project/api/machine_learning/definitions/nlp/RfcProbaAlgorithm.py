from typing import List

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import make_pipeline

from boonai.project.api.machine_learning.definitions.SklearnAlgorithm import \
    SklearnAlgorithm


class RfcProbaAlgorithm(SklearnAlgorithm):
    name = 'RFC Proba'
    description = 'Random Forest for NLP'
    creator = 1  # user id?
    tags = ['nlp', 'text', 'reports', 'rf', 'grid-search']
    groups = ['nlp', 'grid-search']
    pipeline = None

    def train(self, x: List[str], y: List[int]):
        pipeline = make_pipeline(
            TfidfVectorizer(),
            RandomForestClassifier()
        )
        parameters = {
            'tfidfvectorizer__use_idf': (True, False),
            'randomforestclassifier__n_estimators': [2, 5, 10, 15, 17, 20, 22, 25, 30, 35, 50, 60, 80, 100, 150],
            'randomforestclassifier__min_samples_split': [2, 3, 4, 5, 10, 20]
        }

        self.pipeline = GridSearchCV(pipeline, cv=3, n_jobs=4, param_grid=parameters)
        self.pipeline.fit(x, y)
        print(self.pipeline.best_params_)

    def predict(self, x: List[str]):
        if self.pipeline is None:
            self.load()
        return self.pipeline.predict_proba(x)

