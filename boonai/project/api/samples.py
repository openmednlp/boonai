from flask import Blueprint, jsonify
from flask_restful import Resource, Api, reqparse

parser = reqparse.RequestParser()
parser.add_argument('labeled_sample')


class Sample(Resource):
    def get(self, dataset_id):
        # Get list of all get
        return jsonify(
            {
                dataset_id: {
                    'col1': [1, 2, 3, 4],
                    'col2': [5, 6, 7, 8],
                    'labels': []
                }
            }
        )

    def post(self, dataset_id, labeled_sample):
        # batch post, could be useful for backups
        args = parser.parse_args()
        print(args)
        return {'you sent': [dataset_id, args['labeled_sample']]}, 201

    def update(self, dataset_id):
        # Overwrite uploaded sample
        return {'never': 'gonna happen dataset all'}, 200

    def delete(self, dataset_id):
        # Delete uploadaed sample
        return {'never': 'gonna happen sample'}, 200


al_blueprint = Blueprint('al', __name__)
data_api = Api(al_blueprint, '/v1')
data_api.add_resource(Sample, '/get/<int:dataset_id>/samples')

