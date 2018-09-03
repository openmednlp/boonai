from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask import current_app, url_for
from flask_wtf.file import FileField, FileRequired

from wtforms import StringField
from wtforms.validators import Length
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename

import requests
from pandas.io.json import json_normalize
import json


mod = Blueprint('site_datasets', __name__, template_folder='templates')


def _get_link(links, rel_value):
    for l in links:
        if l['rel'] == rel_value:
            return l['href']
    raise ValueError('No file relation found in the links list')


@mod.route('/', methods=['GET'])
def root():
    urls = [
        url_for('site_datasets.upload_get'),
        url_for('site_datasets.list')
    ]
    names = [
        'upload',
        'list'
    ]
    return render_template('datasets/index.html', links=zip(urls, names))


class Submit(FlaskForm):
    name = StringField(
        'Dataset Name',
        [Length(min=5, max=25)]
    )
    description = StringField(
        'Dataset Description',
        [Length(min=5, max=35)]
    )
    file = FileField(
        'Dataset File',
        [FileRequired()]
    )


@mod.route('/upload', methods=['POST'])
def upload_post():
    api_url = current_app.config['API_URI']
    datasets_api_url = api_url + '/api/v1/datasets'
    storage_api_url = api_url + '/api/v1/storage'

    form = Submit()

    if form.validate_on_submit():
        # Don't forget the csrf, or it will fail.
        file = request.files['file']
        if not secure_filename(file.name):
            # TODO make this better
            flash('Wrong file name', 'error')
            return render_template(
                "datasets/upload.html",
                form=form,
                url=url_for('site_datasets.upload_get')
            )

        r = requests.post(
            storage_api_url,
            file.read(),
            headers={'Content-Type': 'application/octet-stream'}
        )

        dataset_json = {
            'name': form.name.data,
            'description': form.description.data,
            'file_id': int(r.text)
        }
        requests.post(
            datasets_api_url,
            json=dataset_json
        )

        flash('Thanks for uploading the file')
        return redirect(url_for('site_datasets.upload_get'))

    return redirect(url_for('site_datasets.upload_get')) # fix the checking part


@mod.route('/upload', methods=['GET'])
def upload_get():
    form = Submit()
    # TODO: make a section selection ((.|\n)*(\n)+Beurteilung) ((\n)+tel(.|\n)*)
    return render_template(
        'datasets/upload.html',
        form=form,
        url=url_for('site_datasets.upload_get')
    )


@mod.route('/list/<int:dataset_id>')
def dataset_get(dataset_id):

    api_url = current_app.config['API_URI']
    url = api_url + '/api/v1/datasets/' + str(dataset_id)
    r = requests.get(url)

    json_data = json.loads(r.content)
    url = _get_link(json_data['links'], 'file')
    delete_url = url_for('site_datasets.dataset_delete', dataset_id=dataset_id) #TODO: local url and then from that page 2 actions - delete from get and then from storage (or make a job for that) _get_link(json_data['links'], 'delete') # requests.delete()
    return '''
    <p>
    Id: {}</br>
    Name: {}</br>
    Description:<br/> 
    {}</br>
    <a href={}>link</a> <a href={}>delete</a></p>
    '''.format(
        json_data['content']['id'],
        json_data['content']['name'],
        json_data['content']['description'],
        url,
        delete_url
    )


@mod.route('/list', methods=['GET'])
def list():
    api_url = current_app.config['API_URI']
    datasets_api_url = api_url + '/api/v1/datasets'

    start = request.args.get('start')
    limit = request.args.get('limit')
    if not start:
        start = 1
    else:
        start = int(start)
    if not limit:
        limit = 5
    else:
        limit = int(limit)

    r = requests.get(
        '{}?start={}&limit={}'.format(
            datasets_api_url, start, limit)
    )
    data = json.loads(r.text)
    datasets_df = json_normalize(data['content'])
    urls = [
        url_for('site_datasets.dataset_get', dataset_id=dataset_id)
        for dataset_id
        in datasets_df['id']
    ]
    names = datasets_df['name']

    prev_attributes = [
        l['href']
        for l in data['links']
        if l['rel'] == 'previous'
    ][0].split('?')[-1]

    prev_url = None
    if prev_attributes:
        prev_url = '{}?{}'.format(
            request.path,
            prev_attributes
        )

    next_attributes = [
        l['href']
        for l in data['links']
        if l['rel'] == 'next'
    ][0].split('?')[-1]

    next_url = None
    if next_attributes:
        next_url = '{}?{}'.format(
            request.path,
            next_attributes
        )

    return render_template(
        'datasets/list.html',
        url=url_for('site_datasets.list'),
        links=zip(urls, names),
        prev_url=prev_url if prev_url else None,
        next_url=next_url if next_url else None
    )

@mod.route('/list/<int:dataset_id>/delete')
def dataset_delete(dataset_id):
    api_url = current_app.config['API_URI']
    dataset_url = api_url + '/api/v1/datasets/' + str(dataset_id)
    r = requests.get(dataset_url)

    json_data = json.loads(r.content)
    file_url = _get_link(json_data['links'], 'file')

    r_dataset = requests.delete(dataset_url)
    r_file = requests.delete(current_app.config['API_URI'] + file_url)

    return 'Delete is not implemented on the API side atm' # TODO: make real response
