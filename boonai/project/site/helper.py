from flask import current_app
import requests
from flask_paginate import Pagination, get_page_parameter
import re
import pandas as pd
import io


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


def extract_section(header_patterns, string, strip=True):
    pattern = r'({})[ \t]*\n+((.+\n)+?)\n{{1}}'.format('|'.join(header_patterns))
    findings = re.findall(
        pattern=pattern,
        string=string,
        flags=re.IGNORECASE
    )

    if findings:
        result = '\n'.join([f[1] for f in findings])
        if strip:
            return result.strip()

    return ''


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
    params['page_data'] = df.loc[start:end].values.tolist()

    return params


def url_join(base_url, url):
    return '/'.join([base_url.strip('/'), str(url)])


def url_csv_to_df(url):
    csv_content = requests.get(url).content
    return pd.read_csv(
        io.StringIO(
            csv_content.decode('utf-8')
        )
    )