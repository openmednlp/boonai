from flask import Blueprint, jsonify, request, url_for, abort
from flask_restful import Resource, Api
from boonai.model import Dataset
from boonai.project import db
from flask import current_app
from boonai.project.site.helper import url_join


def row_to_dict(row):
    return dict(
        (col, getattr(row, col))
        for col
        in row.__table__.columns.keys()
    )


def get_paginated_list(results, url, start, limit):
    # check if page exists
    count = len(results)

    if count == 0:
        return {
            'start': start,
            'limit': limit,
            'count': count,
            'previous': '',
            'next': '',
            'field_selection': []
        }

    if count < start:
        abort(404)

    # make response
    obj = {
        'start': start,
        'limit': limit,
        'count': count
    }

    # make URLs
    # make previous url
    if start == 1:
        obj['previous'] = ''
    else:
        start_previous = max(1, start - limit)
        limit_previous = max(limit, start - 1 - start_previous)
        obj['previous'] = url + '?start={}&limit={}'.format(start_previous, limit_previous)

    # make next url
    if start + limit > count:
        obj['next'] = ''
    else:
        start_copy = start + limit
        obj['next'] = url + '?start={}&limit={}'.format(start_copy, limit)

    # finally extract result according to bounds
    obj['field_selection'] = results[(start - 1):(start - 1 + limit)]
    return obj


class All(Resource):
    def get(self):
        storage_api_url = current_app.config['STORAGE_API']

        user_id = request.args.get('userid')
        project_id = request.args.get('projectid')
        query = Dataset.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        if project_id:
            query = query.filter_by(project_id=project_id)
        datasets = query.all()  # TODO: add admin and None if not logged in - security risk!

        content = [{
            'id': d.id,
            'file_id': d.file_id,
            'name': d.name,
            'description': d.description,
            'train': d.train,
            'test': d.test,
            'label': d.label,
            'user_id': d.user_id,
            'project_id': d.project_id,
            'links': [
                {
                    "rel": "self",
                    "href": url_join(request.base_url, d.id)
                }, {
                    "rel": "file",
                    "href": url_join(storage_api_url, d.file_id)
                }]
        } for d in datasets]

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
            file_id=posted_json['file_id']
        )

        db.session.add(dataset)
        db.session.commit()

        return {'you sent': dataset.id}, 201

    #  TODO: batch update missing?
    def delete(self):
        # it's gonna delete everything
        # Dangerous, maybe jsut for super duper admin user
        return {'never': 'gonna happen dataset all'}, 200


class Single(Resource):
    def get(self, dataset_id):
        storage_api_url = current_app.config['STORAGE_API']
        # get sepcific model
        dataset = Dataset.query.filter_by(id=dataset_id).first()
        content = row_to_dict(dataset)
        return jsonify(
            {
                'content': content,
                'links': [
                    {
                        "rel": "self",
                        "href": url_join(request.base_url, dataset_id)
                    },
                    {
                        "rel": "file",
                        "href": url_join(
                            storage_api_url,
                            content['file_id']
                        )
                    }
                ]

            }
        )


data_blueprint = Blueprint('datasets', __name__)
data_api = Api(data_blueprint, '/v1')
data_api.add_resource(All, '/datasets')
data_api.add_resource(Single, '/datasets/<int:dataset_id>')
