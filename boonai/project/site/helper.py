import io
from io import StringIO

import json
import re

import pandas as pd
import requests
from flask import current_app, jsonify
from flask_paginate import Pagination, get_page_parameter


def upload_dataset(file, name, description, user_id, project_id):
    datasets_api_url = current_app.config['DATASETS_API']
    storage_api_url = current_app.config['STORAGE_API']
    r = requests.post(
        storage_api_url,
        file,
        headers={'Content-Type': 'application/octet-stream'}
    )

    dataset_json = {
        'name': name,
        'description': description,
        'file_id': int(r.text),
        'user_id': int(user_id),
        'project_id': int(project_id)
    }
    requests.post(
        datasets_api_url,
        json=dataset_json
    )
    return True


from os.path import splitext


def get_file_type(filename):
    ext = splitext(filename)[1]
    if ext == '.csv':
        return 'csv'
    if ext in ['.xls', '.xlsx']:
        return 'excel'


def extract_section(header_patterns, string, strip=True, empty_value=''):
    pattern = r'({})[ \t]*:?[ \t]*\n+((.+\n)+?)(\n|\Z){{1}}'.format('|'.join(header_patterns))
    findings = re.findall(
        pattern=pattern,
        string=string,
        flags=re.IGNORECASE
    )

    if findings:
        result = '\n'.join([f[1] for f in findings])
        if strip:
            return result.strip()

    return empty_value


def get_css_framework():
    return current_app.config.get('CSS_FRAMEWORK', 'bootstrap4')


def get_link_size():
    return current_app.config.get('LINK_SIZE', 'sm')


def get_alignment():
    return current_app.config.get('LINK_ALIGNMENT', '')


def show_single_page_or_not():
    return current_app.config.get('SHOW_SINGLE_PAGE', False)


def get_pagination(**kwargs):
    kwargs.setdefault('record_name', 'records')
    return Pagination(css_framework=get_css_framework(),
                      link_size=get_link_size(),
                      alignment=get_alignment(),
                      show_single_page=show_single_page_or_not(),
                      **kwargs
                      )


def get_html_pagination_params(request_args, df, record_name='dataset'):
    search = False
    q = request_args.get('q')
    if q:
        search = True

    page = request_args.get(get_page_parameter(), type=int, default=1)
    row_count = len(df)

    per_page = 5

    params = dict()
    params['pagination'] = get_pagination(
        page=page,
        per_page=per_page,
        total=row_count,
        search=search,
        record_name=record_name
    )

    start = (page - 1) * per_page
    end = start + per_page - 1
    params['page_data'] = (
        []
        if df.empty
        else df.loc[start:end].values.tolist()
    )

    return params


def url_join(*args):
    return '/'.join([str(arg) for arg in args])


def url_csv_to_df(url):
    csv_content = requests.get(url).content
    return pd.read_csv(
        io.StringIO(
            csv_content.decode('utf-8')
        )
    )


def get_dataset_response(dataset_id):
    datasets_api = current_app.config['DATASETS_API']
    dataset_uri = url_join(datasets_api, dataset_id)
    return requests.get(dataset_uri)


def dataset_id_to_df(dataset_id):
    datasets_api = current_app.config['DATASETS_API']
    dataset_uri = url_join(datasets_api, dataset_id)
    r_dataset = requests.get(dataset_uri)
    dataset_links = r_dataset.json()['links']

    # TODO: helper function for this exists
    storage_uri = [
        l['href']
        for l in dataset_links
        if l['rel'] == 'binary'
    ][0]

    r_storage = requests.get(storage_uri)
    dataset = r_storage.content.decode('utf-8')
    csv = StringIO(dataset)
    return pd.read_csv(csv)


def hateoas_get_link(single_json, lookup_str, links='links', rel='rel', href='href'):
    links = single_json[links]
    for l in links:
        if l[rel] == lookup_str:
            return l[href]
    raise ValueError('No file relation found in the links list')


def get_available_fields(dataset_id):
    dataset_api_url = current_app.config['DATASETS_API']
    dataset_url = url_join(dataset_api_url, dataset_id)
    r = requests.get(dataset_url)
    content = json.loads(r.content)
    links = content['links']

    file_url = None
    for l in links:
        if l['rel'] == 'binary':
            file_url = l['href']
            break

    df = url_csv_to_df(file_url)

    return jsonify({c: c for c in df.columns})
