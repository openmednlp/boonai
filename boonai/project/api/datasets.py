from flask import Blueprint, jsonify, request, url_for, abort
from flask_restful import Resource, Api
from flask_user import current_user
from boonai.model import Dataset
from boonai.project import db


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
            'results': []
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
    obj['results'] = results[(start - 1):(start - 1 + limit)]
    return obj


class All(Resource):
    def get(self):
        # Get list of all get

        start = request.args.get('start')
        limit = request.args.get('limit')

        if not start:
            start = 1
        else:
            start = int(start)
        if not limit:
            limit = 1000
        else:
            limit = int(limit)

        datasets = Dataset.query.all()

        # if len(datasets) == 0:


        dataset_pages = get_paginated_list(
            datasets,
            url_for('datasets.all'),
            start,
            limit
        )


        datasets_dict = [
            row_to_dict(row)
            for row in dataset_pages['results']
         ]

        for dataset_dict in datasets_dict:
            dataset_dict['links'] = [
                {
                    "rel": "self",
                    "href": url_for('datasets.single', dataset_id=dataset_dict['id'])
                 },
                {
                    "rel": "file",
                    "href": url_for('storage.single', file_id=dataset_dict['file_id'])
                }
            ]

        return {
            'content': datasets_dict,
            'links': [
                {
                    "rel": "self",
                    "href": request.full_path
                },
                {
                    "rel": "previous",
                    "href": dataset_pages['previous']
                },
                {
                    "rel": "next",
                    "href": dataset_pages['next']
                }
            ]
        }

    def post(self):
        # Add new dataset
        posted_json = request.get_json()

        dataset = Dataset(
            name=posted_json['name'],
            description=posted_json['description'],
            user_id=current_user.get_id(),
            project_id=current_user.get_id(),
            file_id=posted_json['file_id']
        )

        db.session.add(dataset)
        db.session.commit()

        return {'you sent': dataset.id}, 201


    # TODO: batch update missing?

    def delete(self):
        # it's gonna delete everything
        # Dangerous, maybe jsut for super duper admin user
        return {'never': 'gonna happen dataset all'}, 200


class Single(Resource):
    def get(self, dataset_id):
        # get sepcific model
        dataset = Dataset.query.filter_by(id=dataset_id).first()
        dict = row_to_dict(dataset)
        return jsonify(
            {
                'content': dict,
                'links': [
                    {
                        "rel": "self",
                        "href": url_for('datasets.single', dataset_id=dataset_id)
                    },
                    {
                        "rel": "file",
                        "href": url_for('storage.single', file_id=dict['file_id'])
                    }
                ]

            }
        )


data_blueprint = Blueprint('datasets', __name__)
data_api = Api(data_blueprint, '/v1')
data_api.add_resource(All, '/datasets')
data_api.add_resource(Single, '/datasets/<int:dataset_id>')
