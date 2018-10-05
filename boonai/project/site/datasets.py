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
from pandas.errors import EmptyDataError

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
        url_for('site_dataprep.dropzone'),
        url_for('site_datasets.dataset_list')
    ]
    names = [
        'dropzone',
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


@mod.route('/list/<int:dataset_id>')
@login_required
def dataset_get(dataset_id):
    dataset_api_url = current_app.config['DATASETS_API']
    dataset_info_url = '/'.join([s.strip('/') for s in [dataset_api_url, str(dataset_id)]])
    r = requests.get(dataset_info_url)

    if r.status_code != 200:
        flash('Dataset API response code was {}, cannot fetch the dataset'.format(r.status_code), 'warning')
        return redirect(url_for('site_datasets.dataset_list'))

    json_data = json.loads(r.content)
    dataset_file_url = _get_link(json_data['links'], 'file')
    delete_url = url_for(
        'site_datasets.dataset_delete',
        dataset_id=dataset_id
    )

    r_storage = requests.get(dataset_file_url)
    if r_storage.status_code != 200:
        flash('Storage API response code was {}, cannot fetch the file'.format(r.status_code), 'warning')
        return redirect(url_for('site_datasets.dataset_list'))

    csv_content = r_storage.content
    try:
        df = pd.read_csv(
            io.StringIO(
                csv_content.decode('utf-8')
            )
        )
    except EmptyDataError:
        flash('Could not make a dataset out of the storage file - it is empty', 'warning')
        return redirect(url_for('site_datasets.dataset_list'))

    if df.empty:
        flash('Cannot show dataset - it is empty', 'warning')

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
    )


@mod.route('/list', methods=['GET'])
@login_required
def dataset_list():
    datasets_api_url = current_app.config['DATASETS_API']

    params = {'userid': current_user.id}
    r = requests.get(datasets_api_url, params=params)

    if r.status_code != 200:
        flash('Could not get the dataset list from the Dataset API', 'warning')
        return redirect(url_for('site_datasets.root'))

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
    dataset_api_url = current_app.config['DATASETS_API']
    dataset_url = url_join(dataset_api_url, dataset_id)
    r = requests.get(dataset_url)

    json_data = json.loads(r.content)
    file_url = _get_link(json_data['links'], 'file')

    r_dataset = requests.delete(dataset_url)
    r_file = requests.delete(file_url)

    flash('Not yet implemented', 'info')

    return redirect(url_for('.dataset_get', dataset_id=dataset_id))


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
