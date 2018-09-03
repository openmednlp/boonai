from flask import Blueprint, url_for
from flask_restful import Resource, Api
from boonai.project.api.machine_learning.algorithm_selection import algorithms_info, algorithms


def row_to_dict(row):
    return dict(
        (col, getattr(row, col))
        for col
        in row.__table__.columns.keys()
    )


class All(Resource):
    def get(self):
        # Get list of all models
        algorithm_contents = algorithms_info.values()

        content = []
        for algorithm_content in algorithm_contents:
            algorithm_content['links'] = [
                {

                    "rel": "self",
                    "href": url_for(
                        'algorithms.single',
                        uid=algorithm_content['id']
                    )
                }
            ]
            content.append(algorithm_content)
        return {
            'content': content,
            'links': [
                {
                    "rel": "self",
                    "href": url_for('algorithms.all')
                }
            ]
        }


class Single(Resource):
    def get(self, uid):
        # Get list of all models

        return {
            'content': algorithms_info[uid],
            'links': [
                {
                    "rel": "self",
                    "href": url_for('algorithms.single', uid=uid)
                }
            ]
        }


algorithms_blueprint = Blueprint('algorithms', __name__)
api = Api(algorithms_blueprint, '/v1')
api.add_resource(All, '/machine-learning/algorithms')
api.add_resource(Single, '/machine-learning/algorithms/<int:uid>')
