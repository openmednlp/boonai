from flask import Blueprint, abort, current_app, jsonify, request, url_for
from flask_restful import Api, Resource

from boonai.model import Dataset
from boonai.project import db
from boonai.project.site.helper import url_join


def row_to_dict(row):
    return dict(
        (col, getattr(row, col))
        for col
        in row.__table__.columns.keys()
    )


class All(Resource):
    def get(self):
        storage_adapter_api_uri = current_app.config['STORAGE_ADAPTER_API']

        user_id = request.args.get('userid')
        project_id = request.args.get('projectid')
        query = Dataset.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        if project_id:
            query = query.filter_by(project_id=project_id)
        datasets = query.all()  # TODO: add admin and None if not logged in - security risk!

        single = Single()
        content = [single.get(d.id) for d in datasets]

        # TODO: arguments with dict if possible
        self_href = (
            request.base_url +
            '?user_id={}'.format(user_id)
            if user_id
            else ''
        )

        return {
            'content': content,
            'links': [
                {
                    "rel": "self",
                    "href": self_href
                }
            ]

        }

    def post(self):
        # Add new dataset
        posted_json = request.get_json()
        dataset = Dataset(
            name=posted_json['name'],
            description=posted_json['description'],
            user_id=posted_json['user_id'],
            train=posted_json['train'],
            test=posted_json['test'],
            label=posted_json['label'],
            project_id=posted_json['project_id'],
            storage_adapter_uri=posted_json['storage_adapter_uri'],
            binary_uri=posted_json['binary_uri']
        )
        db.session.add(dataset)
        db.session.commit()

        return Single().get(dataset.id), 201

    #  TODO: batch update missing?
    def delete(self):
        # it's gonna delete everything
        # Dangerous, maybe jsut for super duper admin user
        return {'never': 'gonna happen dataset all'}, 200


def get_binary_uri(dataset):
    return dataset.binary_uri


class Single(Resource):
    def get(self, dataset_id):
        # storage_api_url = current_app.config['STORAGE_API']

        dataset = Dataset.query.filter_by(id=dataset_id).first()
        content = row_to_dict(dataset)  # TODO: get uri form DB, not id

        return {
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'do_train': dataset.train,
            'do_test': dataset.test,
            'do_label': dataset.label,
            'user_id': dataset.user_id,
            'project_id': dataset.project_id,
            'links': [
                {
                    "rel": "self",
                    "href": url_join(request.base_url, dataset.id)
                }, {
                    "rel": "storage",
                    "href": dataset.storage_adapter_uri
                },
                {
                    "rel": "label",
                    "href": url_join(request.url_root, 'api', 'v1','active-learning')
                },
                {
                    "rel": "binary",
                    "href": get_binary_uri(dataset)
                }
            ]
        }

    def delete(self, dataset_id):
        # it's gonna delete everything
        # Dangerous, maybe jsut for super duper admin user
        return {'never': 'gonna happen dataset single {}'.format(dataset_id)}, 200


data_blueprint = Blueprint('datasets', __name__)
data_api = Api(data_blueprint, '/v1')
data_api.add_resource(All, '/datasets')
data_api.add_resource(Single, '/datasets/<int:dataset_id>')
