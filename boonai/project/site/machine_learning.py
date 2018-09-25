from flask import Blueprint, render_template, request, redirect, flash
from flask import current_app, url_for
from flask import Response
from flask import jsonify

from flask_wtf.file import FileField, FileRequired

from wtforms import SelectField

from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename

import requests

from pandas import DataFrame
from pandas.io.json import json_normalize

import json
from boonai.project.site.helper import url_join, url_csv_to_df

mod = Blueprint('site_machine_learning', __name__, template_folder='templates')


def _get_link(links, rel_value):
    for l in links:
        if l['rel'] == rel_value:
            return l['href']
    raise ValueError('No file relation found in the links list')


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
    url = url_join(current_app.config['MODELS_API'], str(model_id))
    r = requests.get(url)

    json_data = json.loads(r.content)
    url = _get_link(json_data['links'], 'file')
    # url = api_url + '/api/v1/storage/{}'.format(json_data['file_id'])

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


class TrainForm(FlaskForm):
    # name = StringField(
    #     'Dataset Name',
    #     [Length(min=5, max=25)]
    # )
    # description = StringField(
    #     'Dataset Description',
    #     [Length(min=5, max=35)]
    # )
    dataset = SelectField(label='Dataset', coerce=str)
    algorithm = SelectField(label='Algorithm', coerce=str)
    input = SelectField(label='Input field', coerce=str)
    target = SelectField(label='Target field', coerce=str)


@mod.route('/', methods=['GET'])
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


@mod.route('/train', methods=['GET', 'POST'])
def train():
    dataset_url = current_app.config['DATASETS_API']

    r = requests.get(dataset_url)
    datasets = json.loads(r.content)['content']

    dataset_options = []
    for c in datasets:
        dataset_options.append(
            (
                str(c['id']),
                c['name']
            )
        )
    algorithms_url = current_app.config['ALGORITHMS_API']

    r = requests.get(algorithms_url)
    algorithms = json.loads(r.content)['content']
    algorithm_options = []
    for a in algorithms:
        algorithm_options.append(
            (str(a['id']), a['name'])
        )

    form = TrainForm()
    form.algorithm.choices = algorithm_options
    form.dataset.choices = dataset_options
    form.input.choices = []
    form.target.choices = []

    if form.validate_on_submit():
        dataset_id = form.dataset.data
        algorithm_id = form.algorithm.data

        model_api_url = current_app.config['MODELS_API']
        json_request = {
            "dataset_id": dataset_id,
            "algorithm_id": algorithm_id
        }

        r = requests.post(
            model_api_url,
            json=json_request
        )

        print(r)

        return redirect(url_for('site_machine_learning.train'))

    return render_template(
        'ml/train_form.html',
        form=form,
        url=url_for('site_machine_learning.train')
    )


@mod.route('/train/dataset/<int:dataset_id>', methods=['GET'])
def train_dataset(dataset_id):
    return json.dumps(
        {'id': dataset_id}
    )


@mod.route('/train/dataset/<int:dataset_id>/available-fields', methods=['GET'])
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


class PredictForm(FlaskForm):
    model = SelectField(label='Model', coerce=str)
    dataset_file = FileField('Dataset', [FileRequired()])


@mod.route('/predict', methods=['GET', 'POST'])
def predict():
    models_api_url = current_app.config['MODELS_API']
    r = requests.get(models_api_url)
    models = json.loads(r.content)['content']
    options = [
        (
            str(m['id']),
            'data-{}-algo-{}'.format(
                m['dataset_id'],
                m['algorithm_id']
            )
        ) for m in models
    ]

    form = PredictForm()
    form.model.choices = options
    if form.validate_on_submit():

        # Don't forget the csrf, or it will fail.
        file = request.files['dataset_file']
        if not secure_filename(file.name):
            # TODO make this better
            flash('Wrong file name', 'error')
            return render_template(
                "ml/predict_form.html",
                form=form,
                url=url_for('site_machine_learning.predict')
            )

        api_url = '{}/{}'.format(
                models_api_url,
                form.model.data
        )

        r = requests.post(
            api_url,
            file.read(),
            headers={'Content-Type': 'application/octet-stream'}
        )

        result = r.json()['content']

        df = DataFrame({'X': result['X'], 'y': result['y']})
        csv = df.to_csv()

        return Response(
            csv,
            mimetype="text/csv",
            headers={
                "Content-disposition": "attachment; filename=file.csv"
            }
        )

    return render_template(
        'ml/predict_form.html',
        form=form,
        url=url_for('site_machine_learning.predict')
    )
