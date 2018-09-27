from flask import Blueprint, render_template, request, redirect, flash
from flask import current_app, url_for, jsonify
from flask_wtf.file import FileField, FileRequired

from wtforms import StringField
from wtforms.validators import Length
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename

import requests
from pandas.io.json import json_normalize
import json

from flask_user import login_required, current_user

import pandas as pd
import io

from boonai.project.site.helper import upload_dataset, get_html_pagination_params, url_join, url_csv_to_df

mod = Blueprint('site_datasets', __name__, template_folder='templates')


def _get_link(links, rel_value):
    for l in links:
        if l['rel'] == rel_value:
            return l['href']
    raise ValueError('No file relation found in the links list')


@mod.route('/', methods=['GET'])
@login_required
def root():
    urls = [
        url_for('site_datasets.upload_get'),
        url_for('site_datasets.dataset_list')
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


# TODO: Upload section is obsolete - data prep covers this part now
@mod.route('/upload', methods=['GET'])
@login_required
def upload_get():
    form = Submit()
    return render_template(
        'datasets/upload.html',
        form=form,
        url=url_for('site_datasets.upload_get')
    )


@mod.route('/upload', methods=['POST'])
@login_required
def upload_post():
    form = Submit()
    if not form.validate_on_submit():
        return redirect(url_for('site_datasets.upload_get'))

    file = request.files['file']
    if not secure_filename(file.name):
        # TODO make this better
        flash('Wrong file name', 'error')
        return render_template(
            "datasets/upload.html",
            form=form,
            url=url_for('site_datasets.upload_get')
        )
    name = form.name.data
    description = form.description.data
    upload_dataset(
        file.read(),
        name,
        description,
        user_id=current_user.id,
        project_id=0)  # TODO Project ID is fake

    flash('Thanks for uploading the file')

    return redirect(url_for('site_datasets.upload_get'))


@mod.route('/list/<int:dataset_id>')
@login_required
def dataset_get(dataset_id):
    dataset_api_url = current_app.config['DATASETS_API']
    dataset_info_url = '/'.join([s.strip('/') for s in [dataset_api_url, str(dataset_id)]])
    r = requests.get(dataset_info_url)

    json_data = json.loads(r.content)
    dataset_file_url = _get_link(json_data['links'], 'file')
    delete_url = url_for(
        'site_datasets.dataset_delete',
        dataset_id=dataset_id
    )
    # TODO:
    # local url and then from that page 2 actions delete from get and then from storage
    # (or make a job for that)
    # _get_link(json_data['links'], 'delete') # requests.delete()

    # TODO: Use helper
    csv_content = requests.get(dataset_file_url).content
    df = pd.read_csv(
        io.StringIO(
            csv_content.decode('utf-8')
        )
    )

    html_params = get_html_pagination_params(
        request.args,
        df
    )

    return render_template(
        'datasets/info.html',
        info=json_data['content'],
        data=html_params['page_data'],
        pagination=html_params['pagination'],
        download_url=dataset_file_url,
        delete_url=delete_url,
        # url=url_for('site_dataprep.field_selection_get')
    )


@mod.route('/list', methods=['GET'])
@login_required
def dataset_list():
    datasets_api_url = current_app.config['DATASETS_API']

    r = requests.get(
        '{}?userid={}'.format(
            datasets_api_url,
            current_user.id)
    )  # TODO: better params submit

    data = r.json()

    datasets_df = json_normalize(data['content'])

    urls = []
    names = []
    if data['content']:
        urls = [
            url_for('site_datasets.dataset_get', dataset_id=dataset_id)
            for dataset_id
            in datasets_df['id']
        ]
        names = datasets_df['name']

    return render_template(
        'datasets/list.html',
        url=url_for('site_datasets.dataset_list'),
        links=zip(urls, names)
    )


@mod.route('/list/<int:dataset_id>/delete')
@login_required
def dataset_delete(dataset_id):
    api_url = current_app.config['API_URI']
    dataset_url = api_url + '/api/v1/datasets/' + str(dataset_id)
    r = requests.get(dataset_url)

    json_data = json.loads(r.content)
    file_url = _get_link(json_data['links'], 'file')

    r_dataset = requests.delete(dataset_url)
    r_file = requests.delete(current_app.config['API_URI'] + file_url)

    return 'Delete is not implemented on the API side atm'  # TODO: make real response


@mod.route('/<int:dataset_id>/fields', methods=['GET'])
@login_required
def get_available_fields(dataset_id):
    dataset_api_url = current_app.config['DATASETS_API']
    dataset_url = url_join(dataset_api_url, str(dataset_id))
    r = requests.get(dataset_url)
    content = json.loads(r.content)
    links = content['links']

    file_url = None
    for l in links:
        if l['rel'] == 'file':
            file_url = l['href']
            break

    df = url_csv_to_df(file_url)

    return jsonify({c: c for c in df.columns})
