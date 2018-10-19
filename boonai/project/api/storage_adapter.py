import io

import requests
from flask import (Blueprint, abort, current_app, jsonify, request, send_file,
                   url_for)
from flask_restful import Api, Resource

from boonai.model import StorageAdapter
from boonai.project import db
from boonai.project.site import helper as h


def row_to_dict(row):
    if row is None:
        return {}
    return dict(
        (col, getattr(row, col))
        for col
        in row.__table__.columns.keys()
    )


def post_local(uri, bin_data):
    storage_id = requests.post(uri, bin_data).json()
    return h.url_join(uri, storage_id)


def get_local(uri):
    return requests.get(uri).content


storage_engine = {
    'local': (post_local, get_local)
}
engine_name = 'local' # TODO: Put this in settings


class All(Resource):
    def get(self):
        # Get list of all files
        storage_adapter_entities = StorageAdapter.query.with_entities(StorageAdapter.id).all()
        single = Single()
        storage_adapter_entities_json = [
            single.get(row.id) for row in storage_adapter_entities
        ]

        return {
            'content': storage_adapter_entities_json,
            'links': [
                {
                    "rel": "self",
                    "href": url_for('storage.all')
                }
            ]
        }

    def post(self):
        # Add new file
        storage_api_url = current_app.config['STORAGE_API']
        storage_post, _ = storage_engine[engine_name]
        posted_data = request.get_data()
        uri = storage_post(storage_api_url, posted_data)

        storage_adapter_object = StorageAdapter()
        storage_adapter_object.uri = uri

        db.session.add(storage_adapter_object)
        db.session.commit()

        single = Single()
        return single.get(storage_adapter_object.id), 201

    #  TODO: batch update missing?
    def delete(self):
        # it's gonna delete everything
        # Dangerous, maybe jsut for super duper admin user
        return {'never': 'gonna happen dataset all'}, 200


class Single(Resource):
    def get(self, storage_adapter_id):
        storage_adapter_object = StorageAdapter.query.filter_by(id=storage_adapter_id).first()

        content = dict()
        content['id'] = storage_adapter_id
        content['links'] = [
            {
                "rel": "self",
                "href": url_for(
                    'storage_adapter.single',
                    storage_adapter_id=storage_adapter_object.id,
                    _external=True
                )
            },
            {
                "rel": "binary",
                "href": url_for(
                    'storage_adapter.binary',
                    storage_adapter_id=storage_adapter_object.id,
                    _external=True
                )
            }
        ]
        return content


class Binary(Resource):
    def get(self, storage_adapter_id):
        storage_adapter = StorageAdapter.query.filter_by(id=storage_adapter_id).first()
        if storage_adapter is None:
            return abort(404)

        storage_dict = row_to_dict(storage_adapter)

        _, get = storage_engine[engine_name]
        data = get(storage_dict['uri'])

        return send_file(
            io.BytesIO(data),
            mimetype='application/octet-stream',
            as_attachment=True,
            attachment_filename='%s.data' % storage_adapter_id)


storage_adapter_blueprint = Blueprint('storage_adapter', __name__)
storage_adapter_api = Api(storage_adapter_blueprint, '/v1')
storage_adapter_api.add_resource(All, '/storage-adapter')
storage_adapter_api.add_resource(Single, '/storage-adapter/<int:storage_adapter_id>')
storage_adapter_api.add_resource(Binary, '/storage-adapter/<int:storage_adapter_id>/binary')
