import io
import json

import pandas as pd
import requests
from flask import (Blueprint, Response, current_app, flash, redirect,
                   render_template, url_for)
from flask_user import current_user, login_required
from flask_wtf import FlaskForm
from pandas.io.json import json_normalize
from wtforms import SelectField, StringField
from wtforms.validators import Length

from boonai.project.site import helper as h
from boonai.project.site.datasets import get_available_fields

mod = Blueprint('site_machine_learning', __name__, template_folder='templates')


class TrainForm(FlaskForm):
    name = StringField(
        'Dataset Name',
        [Length(min=1, max=50)]
    )
    description = StringField(
        'Dataset Description',
        [Length(min=1, max=500)]
    )
    dataset = SelectField(label='Dataset', coerce=str)
    algorithm = SelectField(label='Algorithm', coerce=str)
    input = SelectField(label='Input field')
    target = SelectField(label='Target field')


class PredictForm(FlaskForm):
    dataset = SelectField(label='Dataset', coerce=str)
    input = SelectField(label='Input field')
    model = SelectField(label='Model')
    type = SelectField(
        label='Type',
        choices=[('excel', 'excel'), ('csv', 'csv')]
    )


# TODO: This is not used at the moment
@mod.route('/models', methods=['GET'])
def models_get():
    models_api_url = current_app.config['MODELS_API']
    r = requests.get(models_api_url)

    data = json.loads(r.text)
    if not data['content']:
        return 'De nada'

    models_df = json_normalize(data['content'])

    urls = [
        url_for('site.dataset', model_id=model_id)
        for model_id
        in models_df['id']
    ]
    names = models_df['name']

    downlaod_section = render_template(
        "url_list.html",
        links=zip(urls, names)
    )

    return "<h1>Fake page</h1>"


@mod.route('/models', methods=['POST'])
def models_post():
    return 'Karamba, you cannot do that! Go to the machine learning site section to train the model.'


@mod.route('/models/<int:model_id>')
def model(model_id):
    url = h.url_join(current_app.config['MODELS_API'], str(model_id))
    r = requests.get(url)

    json_data = json.loads(r.content)
    url = h.hateoas_get_link(json_data, 'file') # TODO: fix this

    return '''
    <p>
    Id: {}</br>
    Name: {}</br>
    Description:<br/> 
    {}</br>
    <a href={}>link</a></p>
    '''.format(
        json_data['content']['id'],
        json_data['content']['name'],
        json_data['content']['description'],
        url
    )


@mod.route('/', methods=['GET'])
@login_required
def root():
    urls = [
        url_for('site_machine_learning.train'),
        url_for('site_machine_learning.predict')
    ]
    names = [
        'train',
        'predict'
    ]
    return render_template('ml/index.html', links=zip(urls, names))


def get_user_datasets_choices(user_id):
    dataset_url = current_app.config['DATASETS_API']

    params = {'userid': user_id}
    r = requests.get(dataset_url, params=params)
    datasets = json.loads(r.content)['content']

    dataset_options = []
    for c in datasets:
        dataset_options.append(
            (
                str(c['id']),
                c['name']
            )
        )

    return dataset_options


@mod.route('/train', methods=['GET', 'POST'])
@login_required
def train():
    algorithms_url = current_app.config['ALGORITHMS_API']

    r = requests.get(algorithms_url)
    if r.status_code not in (200, 201):
        flash(
            'Could not retrieve algorithms - '
            'error code: {}'.format(r.status_code),
            'danger'
        )
        return redirect(url_for('site_machine_learning.root'))

    algorithms = json.loads(r.content)['content']
    algorithm_options = []
    for a in algorithms:
        algorithm_options.append(
            (str(a['id']), a['name'])
        )

    form = TrainForm()
    form.algorithm.choices = algorithm_options

    dataset_options = get_user_datasets_choices(current_user.id)
    if not dataset_options:
        flash('Upload some datasets first', 'warning')
        return redirect(url_for('site_machine_learning.root'))

    form.dataset.choices = dataset_options

    if form.is_submitted():
        selected_dataset_value = form.dataset.data
    else:
        selected_dataset_value = dataset_options[0][0]

    fields_dict = get_available_fields(selected_dataset_value).json.items()

    form.input.choices = fields_dict
    form.target.choices = fields_dict

    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data

        dataset_id = form.dataset.data
        algorithm_id = form.algorithm.data

        model_api_url = current_app.config['MODELS_API']
        json_request = {
            'name': name,
            'description': description,
            "dataset_id": dataset_id,
            "algorithm_id": algorithm_id,
            "user_id": current_user.id,
            "project_id": 0
        }

        r = requests.post(
            model_api_url,
            json=json_request
        )
        if r.status_code not in (200, 201):
            if 500 <= r.status_code < 600:
                flash(
                    'Training failed - the model API call '
                    'returned code: {}'.format(r.status_code),
                    'warning'
                )
            else:
                flash('Something is not right, check if fields are the correct type', 'danger')
            return redirect(url_for('site_machine_learning.train'))

        flash('The model has been trained', 'success')
        return redirect(url_for('site_machine_learning.train'))

    return render_template(
        'ml/train_form.html',
        form=form,
        url=url_for('site_machine_learning.train')
    )


@mod.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    models_api_url = current_app.config['MODELS_API']

    params = {'userid': current_user.id}
    r = requests.get(models_api_url, params=params)

    models_response = r.json()

    model_resources_dict = dict()
    model_choices = []
    for model_dict in models_response['content']:
        model_id = str(model_dict['id'])
        choice = (model_id, model_dict['name'])
        model_choices.append(choice)
        # TODO: rename to resources or so
        model_resources_dict[model_id] = model_dict['resources']

    form = PredictForm()

    form.model.choices = model_choices

    dataset_choices = get_user_datasets_choices(current_user.id)
    form.dataset.choices = dataset_choices

    if not dataset_choices or not model_choices:
        if not dataset_choices:
            flash('Upload some datasets first', 'warning')
        if not model_choices:
            flash('No models - try training some first', 'warning')
        return redirect(url_for('site_machine_learning.root'))

    if form.is_submitted():
        selected_dataset_value = form.dataset.data
    else:
        selected_dataset_value = dataset_choices[0][0]

    fields_dict = get_available_fields(selected_dataset_value).json.items()
    form.input.choices = fields_dict

    if form.validate_on_submit():
        post_json = {
            'dataset_id': form.dataset.data,
            'input_field': form.input.data,
            'user_id': current_user.id,
            'project_id': '',
            'resources': model_resources_dict[form.model.data ]
        }

        r = requests.post(
            h.url_join(models_api_url, form.model.data),
            json=post_json
        )

        if r.status_code not in (200, 201):
            flash(
                'Prediction failed - model API call '
                'returned code: {}'.format(r.status_code),
                'warning'
            )
            return redirect(url_for('site_machine_learning.predict'))

        result = r.json()['content']
        df = pd.read_json(result)

        export_type = form.type.data
        if export_type == 'excel':
                output = io.BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                df.to_excel(writer, sheet_name='Sheet1', encoding='utf-8')
                writer.save()
                result = output.getvalue()
                mimetype = "application/vnd.ms-excel"
                filename = 'result.xlsx'
        elif export_type == 'csv':
            result = df.to_csv(encoding='utf-8')
            mimetype = "text/csv"
            filename = 'result.csv'
        else:
            flash('Nonexistent export type', 'danger')
            return redirect(url_for('.predict'))

        return Response(
            result,
            mimetype=mimetype,
            headers={
                "Content-disposition": "attachment; filename={}".format(filename)
            }
        )

    return render_template(
        'ml/predict_form.html',
        form=form,
        url=url_for('site_machine_learning.predict')
    )
