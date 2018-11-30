from boonai.project.site import helper as h

from flask import Blueprint, redirect, render_template, url_for, flash
from flask import current_app, Response
from flask_user import login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
import io
import json
from os.path import splitext
import pandas as pd
import requests

from werkzeug.utils import secure_filename
from wtforms import SelectMultipleField, SubmitField


mod = Blueprint('site_al', __name__, template_folder='templates')


class DatasetFieldsForm(FlaskForm):
    selected = SelectMultipleField(u'Inputs and Targets')


class DownloadForm(FlaskForm):
    csv_download = SubmitField(label='.csv')
    xls_download = SubmitField(label='.xls')


class UpdateForm(FlaskForm):
    file = FileField(
        'Dataset File',
        [FileRequired()]
    )

#
# def get_dataset(base_url, dataset_id):
#     dataset_single_uri = h.url_join(
#         base_url,
#         dataset_id
#     )
#     r = requests.get(dataset_single_uri)
#
#     if int(r.status_code) != 200:
#         flash(
#             'Dataset API response code was {}, '
#             'cannot fetch the dataset'.format(r.status_code),
#             'warning'
#         )
#         return redirect(url_for('site_datasets.dataset_list'))
#
#     return json.loads(r.content)
#

# def get_al_df(dataset_id):
#     base_url = current_app.config['DATASETS_API'],
#     dataset = get_dataset(base_url, dataset_id)
#
#     h.url_dataset_to_df()
#     storage_binary_uri = h.hateoas_get_link(dataset, 'binary')
#     r_storage = requests.get(storage_binary_uri)
#     if r_storage.status_code != 200:
#         flash('Storage API response code was {}, cannot fetch the file'.format(r.status_code), 'warning')
#         return redirect(url_for('site_datasets.dataset_list'))
#
#     csv_content = r_storage.content


def mark_for_labeling(dataset_id):
    dataset_api = current_app.config['DATASETS_API']
    al_uri = h.url_join(dataset_api, dataset_id, 'al')
    return requests.get(al_uri)

import chardet
from csv import Sniffer
import csv
import codecs

@mod.route('/list/<dataset_id>/al', methods=['GET', 'POST'])
@login_required
def al(dataset_id):
    form_update = UpdateForm()
    form_generate = DownloadForm()
    if form_update.validate_on_submit():
        r_dataset = h.get_dataset_response(dataset_id)
        dataset_json = r_dataset.json()
        storage_adapter_uri = h.hateoas_get_link(dataset_json, 'storage')

        f = form_update.file.data
        filename = secure_filename(f.filename)

        file_type = h.get_file_type(filename)
        if file_type == 'excel':
            df = pd.read_excel(f, encoding='utf-8')
        elif file_type != 'csv':
            raise ValueError(
                'Expected Excel or csv file, received ' + file_type
            )
        else:
            df = pd.read_csv(f, encoding='utf-8')

        #
        # encoding = encoding_info_dict = chardet.detect(f)
        # sniffer = Sniffer()
        # line = f.readline().encode(encoding).decode('utf-8')
        # dialect = sniffer.sniff(line)
        # reader = csv.reader(
        #     codecs.EncodedFile(f, "utf-8"), delimiter=',', dialect=dialect)
        # csv_data = reader

        csv_data = df.to_csv(index=False, encoding='utf-8').encode('utf-8')
        r_put = requests.put(
            storage_adapter_uri,
            data=csv_data
        )

        r_dataset.json()
        flash(
            "Updated dataset's file '{}' (id: {}) with '{}') ".format(
                dataset_json['name'],
                dataset_json['id'],
                filename
            ),
            'success'
        )
        return redirect(url_for('.al', dataset_id=dataset_id))

    if form_generate.validate_on_submit():
        mark_for_labeling(dataset_id)

        df = h.dataset_id_to_df(dataset_id)

        if form_generate.csv_download.data:
            result = df.to_csv(encoding='utf-8')
            mimetype = "text/csv"
            filename = 'result.csv'
        elif form_generate.xls_download.data:
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Sheet1', encoding='utf-8')
            writer.save()
            result = output.getvalue()
            mimetype = "application/vnd.ms-excel"
            filename = 'result.xlsx'
        else:
            flash(
                'Expected one of the buttons to be pushed, '
                'but that did not happen',
                'warning'
            )
            raise ValueError('Form response was neither csl nor xls')

        return Response(
            result,
            mimetype=mimetype,
            headers={
                "Content-disposition": "attachment; filename={}".format(filename)
            }
        )


    return render_template(
        'al/index.html',
        form_generate=form_generate,
        form_update=form_update
    )
