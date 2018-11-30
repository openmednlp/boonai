import io

from flask import Blueprint, abort, jsonify, request, send_file, url_for
from flask_restful import Api, Resource

from boonai.model import Storage
from boonai.project import db

# Backend could be replaced with S3 or anything


def row_to_dict(row):
    if row is None:
        return {}
    return dict(
        (col, getattr(row, col))
        for col
        in row.__table__.columns.keys()
    )


class All(Resource):
    def get(self):
        # Get list of all files
        storages = Storage.query.with_entities(Storage.id).all()
        single = Single()
        storages_json = [single.get(row.id) for row in storages]

        return {
            'content': storages_json,
            'links': [
                {
                    "rel": "self",
                    "href": url_for('storage.all')
                }
            ]
        }

    def post(self):
        # Add new file
        posted_data = request.get_data()

        storage_object = Storage(
            binary=posted_data
        )
        db.session.add(storage_object)
        db.session.commit()

        return storage_object.id, 201


class Single(Resource):
    def get(self, storage_id):
        storage = Storage.query.filter_by(id=storage_id).first()
        if storage is None:
            return abort(404)

        storage_dict = row_to_dict(storage)

        return send_file(
            io.BytesIO(storage_dict['binary']),
            mimetype='application/octet-stream',
            as_attachment=True,
            attachment_filename='%s.data' % storage_id)

    def put(self, storage_id):
        # Update/Replace file
        posted_data = request.get_data()

        storage_row = (
            Storage.query.filter_by(id=storage_id).first()
        )
        storage_row.binary = posted_data
        db.session.commit()

        storage_object = Storage.query.filter_by(id=storage_id).first()
        return storage_object.id



    def delete(self, storage_id):
        # delete a model
        return {'never': 'gonna happen STORAGE single file {}'.format(storage_id)}, 200




storage_blueprint = Blueprint('storage', __name__)
storage_api = Api(storage_blueprint, '/v1')
storage_api.add_resource(All, '/storage')
storage_api.add_resource(Single, '/storage/<int:storage_id>')
