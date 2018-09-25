from flask import Blueprint, jsonify, request, url_for, abort
from flask_restful import Resource, Api
from flask_user import current_user
from boonai.model import File
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

        files = File.query.with_entities(File.id).all()

        file_ids = [
            {'id': row.id}
            for row in files
        ]

        for file_id in file_ids:
            file_id['links'] = [
                {
                    "rel": "self",
                    "href": url_for('storage.single', file_id=file_id['id'])
                 }
            ]

        return {
            'content': file_ids,
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

        file = File(
            content=posted_data
        )

        db.session.add(file)
        db.session.commit()

        return file.id, 201

    #  TODO: batch update missing?
    def delete(self):
        # it's gonna delete everything
        # Dangerous, maybe jsut for super duper admin user
        return {'never': 'gonna happen dataset all'}, 200


class Single(Resource):
    def get(self, file_id):
        # get sepcific model
        files = File.query.filter_by(id=file_id).first()

        if files is None:
            return abort(404)

        file_dict = row_to_dict(files)

        from flask import send_file
        import io
        return send_file(
            io.BytesIO(file_dict['content']),
            mimetype='application/octet-stream',
            as_attachment=True,
            attachment_filename='%s.data' % file_id)

    def delete(self):
        # delete a model
        return {'never': 'gonna happen STORAGE single file'}, 200


storage_blueprint = Blueprint('storage', __name__)
storage_api = Api(storage_blueprint, '/v1')
storage_api.add_resource(All, '/storage')
storage_api.add_resource(Single, '/storage/<int:file_id>')
