from flask import Blueprint, jsonify, request, url_for, current_app, redirect
from flask_restful import Resource, Api
from boonai.model import TrainedModel
from boonai.project.api.machine_learning.algorithm_selection import functions_dict
from boonai.project import db
import requests
import pandas as pd
from io import StringIO
import pickle


def row_to_dict(row):
    return dict(
        (col, getattr(row, col))
        for col
        in row.__table__.columns.keys()
    )


# def create_hateoas(query_result, param_names, param_values):
#
#     query_result_dict = [
#         row_to_dict(row)
#         for row in query_result
#     ]
#     for dict in query_result_dict:
#
#         param_dict = {n: v for n,v in zip(param_names, param_values)}
#         dict['links'] = [
#             {
#                 "rel": "self",
#                 "href": url_for(
#                     'machine_learning.single',
#                     model_id=dict['id']
#                 )
#             },
#             {
#                 "rel": "file",
#                 "href": url_for('storage.single', *param_dict)
#             }
#         ]
#
#     return 'bummer'

class All(Resource):
    def get(self):
        # Get list of all models

        trained_models = TrainedModel.query.all()

        # create_hateoas(trained_models, ['id'], [1])

        trained_models_dict = [
            row_to_dict(row)
            for row in trained_models
        ]

        for model_dict in trained_models_dict:
            model_dict['links'] = [
                {
                    "rel": "self",
                    "href": url_for(
                        'machine_learning_models.single',
                        model_id=model_dict['id']
                    )
                },
                {
                    "rel": "file",
                    "href": url_for('storage.single', file_id=model_dict['file_id'])
                }
            ]

        return {
            'content': trained_models_dict,
            'links': [
                {
                    "rel": "self",
                    "href": url_for('machine_learning_models.all')
                }
            ]
        }

    def post(self):
        # Train the model with a submited dataset and store it

        storage_api = current_app.config['STORAGE_API']
        datasets_api = current_app.config['DATASETS_API']

        posted_json = request.get_json()
        dataset_id = posted_json['dataset_id']
        algorithm_id = int(posted_json['algorithm_id'])

        dataset_uri = datasets_api + '/' + dataset_id
        r_dataset = requests.get(dataset_uri)
        dataset_links = r_dataset.json()['links']
        storage_uri = [
            l['href']
            for l in dataset_links
            if l['rel'] == 'file'
        ][0]

        storage_id = storage_uri.split('/')[-1] # TODO: fix db entries and remove this

        r_storage = requests.get(storage_api + '/' + storage_id)
        dataset = r_storage.content
        csv = StringIO(dataset.decode('cp1252'))
        df = pd.read_csv(csv)

        func = functions_dict[algorithm_id] # TODO disable multithreading, cannot be run from thread

        fitted_model = func(df.ix[:, 0], df.ix[:, 1])
        # TODO: get some stats from training, like test scores

        model_pickle = pickle.dumps(fitted_model)
        r = requests.post(storage_api, data=model_pickle)
        file_id = int(r.content)
        trained_model = TrainedModel(
            name='some name from json form, created prior to this',
            description='some nja nja',
            algorithm_id=int(algorithm_id),
            dataset_id=int(dataset_id),  # TODO enter correct data
            file_id=int(file_id)
        )

        # TODO: Uncomment when done
        db.session.add(trained_model)
        db.session.commit()

        return redirect(
            url_for(
                'machine_learning_models.single',
                model_id=trained_model.id
            )
        )


class Single(Resource):
    def get(self, model_id):
        # get sepcific model
        tm = TrainedModel.query.filter_by(id=model_id).first()
        dict = row_to_dict(tm)
        return {
            'content': dict,
            'links': [
                {
                    "rel": "self",
                    "href": url_for('machine_learning_models.single', model_id=model_id)
                },
                {
                    "rel": "file",
                    "href": url_for('storage.single', file_id=dict['file_id'])
                }
            ]

        }

    def post(self, model_id):
        posted_file = request.get_data()
        csv = StringIO(posted_file.decode('cp1252'))
        df = pd.read_csv(csv)

        tm = TrainedModel.query.filter_by(id=model_id).first()
        storage_api = current_app.config['STORAGE_API']
        r = requests.get('{}/{}'.format(storage_api, tm.file_id))
        pickled_model = r.content
        trained_model = pickle.loads(pickled_model)
        y = trained_model.predict(df.ix[:, 0])

        result = {'X': list(df.ix[:, 0].values), 'y': y.tolist()}

        return jsonify(
            {
                'content': result,
                'links': [
                    {
                        "rel": "self",
                        "href": url_for('machine_learning_models.single', model_id=model_id)
                    }
                ]
            }
        )


models_blueprint = Blueprint('machine_learning_models', __name__)
data_api = Api(models_blueprint, '/v1')
data_api.add_resource(All, '/machine-learning/models')
data_api.add_resource(Single, '/machine-learning/models/<int:model_id>')
