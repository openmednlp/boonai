from boonai.project.site.helper import extract_section, get_html_pagination_params

from flask import Blueprint, render_template, request, redirect, current_app
from flask import url_for, session, flash

from flask_uploads import UploadSet
from flask_user import login_required, current_user

from wtforms import StringField, SelectField, SelectMultipleField, SubmitField, BooleanField
from wtforms.validators import Length
from flask_wtf import FlaskForm

import requests

from pandas import DataFrame

from os.path import join, isfile
from os import listdir
import shutil

from tempfile import mkdtemp
import magic

import pandas as pd
from os.path import splitext

import chardet
from csv import Sniffer

dropzone_files = UploadSet('files')  # allowed file types are defined in the config.

mod = Blueprint('site_dataprep', __name__, template_folder='templates')


class DatasetFieldsForm(FlaskForm):
    selected = SelectMultipleField(u'Inputs and Targets')


class FilterForm(FlaskForm):
    # column = SelectField(u'Column', ['id', 'text'])
    field = SelectField('Field to filter')

    headers = StringField( # TODO : make this extract just a single section
        'Headers',
        render_kw={"placeholder": "headers to extract"}
    )
    keywords = StringField(
        'Filter on keyword',
        render_kw={"placeholder": "extract if contains keyword"}
    )

    test_button = SubmitField()
    submit_button = SubmitField()


class SubmitProcessed(FlaskForm):
    name = StringField(
        'Dataset Name',
        [Length(min=5, max=25)]
    )
    description = StringField(
        'Dataset Description',
        [Length(min=5, max=35)]
    )
    train = BooleanField(
        'Train',
    )
    test = BooleanField(
        'Test',
    )
    label = BooleanField(
        'Label',
    )


def _get_link(links, rel_value):
    for l in links:
        if l['rel'] == rel_value:
            return l['href']
    raise ValueError('No file relation found in the links list')


@mod.route('/dropzone', methods=['GET', 'POST'])
@login_required
def dropzone():
    if request.method == 'POST':
        session['dataset'] = None
        file_items = request.files
        values = file_items.values()
        types = [v.content_type for v in values]

        if not session['content_type']:
            session['content_type'] = types[0]

        if not session['extension']:
            filename = next(iter(file_items.values())).filename
            session['extension'] = splitext(filename)[1]

        is_homogeneous = len(set(types)) == 1
        if is_homogeneous:
            for key in file_items:
                file_path = join(session['tmp_dir'], file_items[key].filename)
                file_items[key].save(file_path)
            return "uploading..."

    if 'tmp_dir' in session and session['tmp_dir']:
        try:
            shutil.rmtree(session['tmp_dir'])
        except FileNotFoundError:
            print('file didn\'t exist')

    session['tmp_dir'] = mkdtemp()
    session['content_type'] = None
    session['extension'] = None
    return render_template('dataprep/dropzone.html')


def texts_to_json(dir_path):
    file_names = listdir(dir_path)
    file_paths = [
        join(dir_path, f)
        for f
        in file_names
        if isfile(join(dir_path, f))
    ]
    m = magic.Magic(mime=True)

    dataset_json = {
        'id': [],
        'text': []
    }

    for file_name, file_path in zip(file_names, file_paths):
        encoding = get_encoding(file_path)

        print(
            'current file {} is {}, ecoding {}'.format(
                file_path,
                m.from_file(file_path),
                encoding
            )
        )

        with open(file_path) as f:
            dataset_json['id'].append(file_name)
            dataset_json['text'].append(f.read().encode(encoding).decode('utf-8'))

    return dataset_json


def get_encoding(file_path):
    with open(file_path, 'rb') as f:
        encoding_info_dict = chardet.detect(f.read())
        print(encoding_info_dict)
    return encoding_info_dict['encoding']


@mod.route('/converter')
@login_required
def converter():
    if not session['extension'] or not session['content_type']:
        flash('Unsupported file type', 'info')
        return redirect(url_for('.dropzone'))

    session['processed'] = False
    session['outputs'] = mkdtemp()

    is_csv = (
            session['extension'] == '.csv' or
            session['content_type'].startswith('text/csv')
    )
    is_excel = session['extension'] in ['.xls', '.xlsx'] or any(
            s
            in session['content_type']
            for s in ['spreadsheet', 'xls', 'xlsx', 'excel']
    )
    is_text = (
            session['extension'] == '.txt' or
            session['content_type'].startswith('text/')
    )

    if is_csv:
        file_name = listdir(session['tmp_dir'])[0]
        file_path = join(session['tmp_dir'], file_name)

        # guess file encoding
        encoding = get_encoding(file_path)

        # guess separator
        with open(file_path, encoding=encoding) as f:
            sniffer = Sniffer()
            line = f.readline().encode(encoding).decode('utf-8')
            dialect = sniffer.sniff(line)

        df = pd.read_csv(file_path, encoding=encoding, dialect=dialect)

        session['fields'] = df.columns.tolist()

    elif is_excel:
        file_name = listdir(session['tmp_dir'])[0]
        file_path = join(session['tmp_dir'], file_name)

        df = pd.read_excel(file_path, encoding='utf-8')
        session['fields'] = df.columns.tolist()

    elif is_text:
        session['fields'] = ['id', 'text']
        dataset_json = texts_to_json(session['tmp_dir'])
        df = DataFrame(dataset_json)

    else:
        flash('Uploaded file types have not been recognized')
        return redirect(url_for('.dropzone'))

    df.to_csv(
        join(session['outputs'], 'original.csv'),
        index=False,
        encoding='utf-8'
    )

    return redirect(url_for('.field_selection_get'))


@mod.route('/field_selection', methods=['GET'])
@login_required
def field_selection_get():
    # redirect to home if no images to display
    session_values = ["fields"]
    if not any(x in session for x in session_values):
        return redirect(url_for('.dropzone'))

    form = DatasetFieldsForm()
    fields = session['fields']
    form.selected.choices = list(zip(fields, fields))

    return render_template(
        'dataprep/field_selection.html',
        datatable=fields,
        form=form,
        url=url_for('.field_selection_get')
    )


@mod.route('/field_selection', methods=['POST'])
@login_required
def field_selection_post():
    session_values = ["fields"]
    if not any(x in session for x in session_values):
        return redirect(url_for('.dropzone'))
    form = DatasetFieldsForm()
    fields = session['fields']
    form.selected.choices = list(zip(fields, fields))

    if form.validate_on_submit():
        session['selected_fields'] = form.selected.data
        df = pd.read_csv(join(session['outputs'], 'original.csv'))
        df = df[session['selected_fields']]
        df.to_csv(
            join(session['outputs'], 'selected_fields.csv'),
            index=False,
            encoding='utf-8'
        )
        # session['headers'] = None
        return redirect(url_for('.filter_data'))

    # TODO: see what to return here
    return url_for('.dropzone')


def process_df(csv_path, process_field, headers_string, keywords_string):
    df = pd.read_csv(csv_path, encoding='utf-8')

    # process headers
    headers = [
        h.strip()
        for h
        in str(headers_string).split(',')
        if len(h.strip()) > 0
    ]
    if headers:
        df[process_field] = df[process_field].apply(
            lambda s: extract_section(headers, s)
        )

    # process keywords
    keywords = [
        k.strip().lower()
        for k
        in str(keywords_string).split(',')
        if len(k.strip()) > 0
    ]
    if keywords:
        df[process_field] = df[process_field].apply(
            lambda s: s if any(str(k) in str(s).lower() for k in keywords) else ''
        )

    non_empty_field_positions = df[process_field] != ''
    df = df[non_empty_field_positions]

    return df.reset_index(drop=True)


@mod.route('/filter', methods=['GET', 'POST'])
@login_required
def filter_data():
    # TODO: check if all necessary values are in the
    session_values = ["selected_fields", "fields", "tmp_dir"]
    if not any(x in session for x in session_values):
        return redirect(url_for('.field_selection_get'))

    processed_csv_path = join(session['outputs'], 'processed.csv')
    selected_fields_csv_path = join(session['outputs'], 'selected_fields.csv')

    form = FilterForm()
    form.field.choices = list(
        zip(
            session['selected_fields'],
            session['selected_fields']
        )
    )

    if form.validate_on_submit():
        session['headers_string'] = form.headers.data
        session['process_field'] = form.field.data
        session['keywords_string'] = form.keywords.data

        df = process_df(
            csv_path=selected_fields_csv_path,
            process_field=session['process_field'],
            headers_string=session['headers_string'],
            keywords_string=session['keywords_string']
        )
        df.to_csv(
            processed_csv_path,
            index=False,
            encoding='utf-8'
        )
        session['processed'] = True

        if form.submit_button.data:
            return redirect(url_for('.upload_proc_get'))
    elif session['processed']:
        df = pd.read_csv(processed_csv_path)
        form.headers.data = session['headers_string']
        form.keywords.data = session['keywords_string']
        form.field.data = session['process_field']
    else:
        df = pd.read_csv(selected_fields_csv_path)

    header_lookalikes = []  # TODO: suggest some headers

    params = get_html_pagination_params(request.args, df, 'imported dataset')

    return render_template(
        'dataprep/filter.html',
        data=params['page_data'],
        pagination=params['pagination'],
        fields=session['selected_fields'],
        form=form,
        url=url_for('.filter_data')
    )


@mod.route('/uploadproc', methods=['GET'])
@login_required
def upload_proc_get():
    form = SubmitProcessed()
    # TODO: make a section selection ((.|\n)*(\n)+Beurteilung) ((\n)+tel(.|\n)*)
    return render_template(
        'datasets/upload.html',
        form=form,
        url=url_for('.upload_proc_get')
    )


def upload_dataset(file, name, description, train, test, label):
    datasets_api_url = current_app.config['DATASETS_API']
    storage_api_url = current_app.config['STORAGE_API']
    try:
        r = requests.post(
            storage_api_url,
            file,
            headers={'Content-Type': 'application/octet-stream'}
        )
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        flash('Could not store file - got HTTPError from the Storage API', 'warning')
        return False

    dataset_json = {
        'name': name,
        'description': description,
        'train': train,  # TODO: maybe it can just accept true false
        'test': test,
        'label': label,
        'file_id': int(r.text),
        'user_id': current_user.id,
        'project_id': 0
    }

    try:
        r = requests.post(
            datasets_api_url,
            json=dataset_json
        )
    except requests.exceptions.HTTPError as err:
        flash('Could not store file - got HTTPError from Dataset API', 'warning')
        return False

    flash('Dataset uploaded', 'success')
    return True


@mod.route('/uploadproc', methods=['POST'])
@login_required
def upload_proc_post():
    if 'processed' in session and session['processed']:
        form = SubmitProcessed()
        file_path = join(session['outputs'], 'processed.csv')
        with open(file_path, 'rb') as f:
            file_content = f.read()
        is_uploaded = upload_dataset(
            file_content,
            name=form.name.data,
            description=form.description.data,
            train= form.train.data,
            test=form.test.data,
            label=form.label.data
        )

        if not is_uploaded:
            return redirect(url_for('.upload_proc_get'))

        return redirect(url_for('site_datasets.root'))
