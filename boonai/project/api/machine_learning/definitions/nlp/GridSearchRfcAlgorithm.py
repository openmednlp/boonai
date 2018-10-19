from typing import List

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import make_pipeline

from boonai.project.api.machine_learning.definitions.SklearnAlgorithm import \
    SklearnAlgorithm


class GridSearchRfcAlgorithm(SklearnAlgorithm):
    name = 'NLP Grid Search RFC'
    description = 'Random Forest for NLP'
    creator = 1  # user id?
    tags = ['nlp', 'text', 'reports']
    groups = ['nlp']
    pipeline = None

    def train(self, x: List[str], y: List[int]):
        pipeline = make_pipeline(
            TfidfVectorizer(),
            RandomForestClassifier()
        )
        parameters = {
            'tfidfvectorizer__use_idf': (True, False),
            'randomforestclassifier__n_estimators': [5, 10, 20],
            'randomforestclassifier__min_samples_split': [2, 3, 5]
        }

        self.pipeline = GridSearchCV(pipeline, cv=3, n_jobs=4, param_grid=parameters)
        self.pipeline.fit(x, y)
