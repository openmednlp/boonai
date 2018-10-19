from io import StringIO
from uuid import uuid4

import pandas as pd
import requests
from flask import Blueprint, current_app, redirect, request, url_for
from flask_restful import Api, Resource
from sqlalchemy.orm import lazyload

from boonai.model import ModelResource, TrainedModel
from boonai.project import db
from boonai.project.api.machine_learning.algorithm_selection import \
    algorithm_dict
from boonai.project.site import helper as h

# TODO move this file level below and rename to ml


def row_to_dict(row):
    return dict(
        (col, getattr(row, col))
        for col
        in row.__table__.columns.keys()
    )


def dataset_id_to_df(dataset_id):
    datasets_api = current_app.config['DATASETS_API']
    dataset_uri = h.url_join(datasets_api, dataset_id)
    r = requests.get(dataset_uri)
    r_dataset = r.json()

    storage_binary_uri = h.hateoas_get_link(r_dataset, 'binary')

    r_binary = requests.get(storage_binary_uri)

    # TODO: This is implementation for for text based problems only
    dataset = r_binary.content.decode('utf-8')
    csv = StringIO(dataset)
    return pd.read_csv(csv)


class All(Resource):
    def get(self):
        # Get list of all models

        user_id = request.args.get('userid')
        project_id = request.args.get('projectid')

        query = TrainedModel.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        if project_id:
            query = query.filter_by(project_id=project_id)
        trained_models = query.options(lazyload('resources')).all()
        trained_model_dicts = []
        # links
        for row in trained_models:
            trained_model = row_to_dict(row)
            trained_model['resources'] = dict()
            for resource in row.resources:
                trained_model['resources'][resource.name] = resource.uri
            trained_model_dicts.append(trained_model)

        return {
            'content': trained_model_dicts,
            'links': [
                {
                    "rel": "self",
                    "href": request.base_url
                }
            ]
        }

    def post(self):
        # Train the model with a submited dataset and store it

        storage_adapter_api = current_app.config['STORAGE_ADAPTER_API']
        datasets_api = current_app.config['DATASETS_API']

        posted_json = request.get_json()
        name = posted_json['name']
        description = posted_json['description']
        dataset_id = posted_json['dataset_id']
        algorithm_id = int(posted_json['algorithm_id'])
        user_id = posted_json['user_id']
        project_id = posted_json['project_id']

        dataset_uri = datasets_api + '/' + dataset_id
        r = requests.get(dataset_uri)
        r_dataset = r.json()

        storage_binary_uri = h.hateoas_get_link(r_dataset, 'binary')

        r_binary = requests.get(storage_binary_uri)

        # TODO: This is implementation for for text based problems only
        dataset = r_binary.content.decode('utf-8')
        csv = StringIO(dataset)
        df = pd.read_csv(csv)

        algorithm = algorithm_dict[algorithm_id](storage_adapter_api)
        algorithm.train(df.ix[:, 0], df.ix[:, 1])
        algorithm.persist()

        trained_model = TrainedModel(
            name=name,
            description=description,
            algorithm_id=int(algorithm_id),
            dataset_id=dataset_uri,  # TODO enter correct data
            user_id=user_id,
            project_id=project_id,
        )
        for key in algorithm.resources:
            resource = ModelResource()
            resource.name = key
            resource.uri = algorithm.resources[key]
            trained_model.resources.append(resource)
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
        content_dict = row_to_dict(tm)

        return {
            'content': content_dict,
            'links': [
                {
                    "rel": "self",
                    "href": h.url_join(
                        request.base_url,
                        model_id
                    )
                }
            ]
        }

    def post(self, model_id):
        posted_json = request.get_json()
        df = dataset_id_to_df(posted_json['dataset_id'])
        x = df.get(posted_json['input_field'][0])

        trained_model = TrainedModel.query.filter_by(id=model_id).first()
        algorithm = algorithm_dict[trained_model.algorithm_id](
            storage_adapter_api=current_app.config['STORAGE_ADAPTER_API']
        )
        algorithm.resources = posted_json['resources']
        algorithm.load()
        result = algorithm.predict(x)

        predicted_column_name = 'predicted'
        predicted_column_name += (
            str(uuid4()) if predicted_column_name in df.keys() else ''
        )
        df[predicted_column_name] = result

        self_href = h.url_join(
            request.base_url,
            'machine_learning_models.single',
            model_id
        )

        return {
            'content': df.to_json(),
            'links': [
                {
                    "rel": "self",
                    "href": self_href
                }
            ]
        }


models_blueprint = Blueprint('machine_learning_models', __name__)
data_api = Api(models_blueprint, '/v1')
data_api.add_resource(All, '/machine-learning/models')
data_api.add_resource(Single, '/machine-learning/models/<int:model_id>')
