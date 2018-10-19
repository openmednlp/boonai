from flask import Flask, url_for
from boonai.model import db, User, Role
import datetime
from flask_user import UserManager
from flask_dropzone import Dropzone

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('boonai.default_settings')
app.config.from_pyfile('application.cfg', silent=True)


# Dropzone settings TODO: move this to a proper location
app.config['DROPZONE_UPLOAD_MULTIPLE'] = True
app.config['DROPZONE_ALLOWED_FILE_CUSTOM'] = True

allowed_file_types = '''
    application/vnd.openxmlformats-officedocument.wordprocessingml.document 
    application/vnd.ms-excel 
    application/vnd.openxmlformats-officedocument.spreadsheetml.sheet  
    application/vnd.ms-excel
    text/csv
    text/plain
    text/x-csv
    '''.split()

app.config['DROPZONE_ALLOWED_FILE_TYPE'] = ','.join(allowed_file_types)
app.config['DROPZONE_REDIRECT_VIEW'] = 'site_dataprep.converter'
app.config['DROPZONE_MAX_FILES'] = 1000
app.config['DROPZONE_MAX_FILE_SIZE'] = 10


db.init_app(app)
db.app = app

dropzone = Dropzone(app)

# Setup Flask-User and specify the User dataset-model
user_manager = UserManager(app, db, User)


# Create all database tables
db.create_all()

# Create 'member@example.com' user with no roles
if not User.query.filter(User.email == 'member@example.com').first():
    user = User(
        username='member',
        email='member@example.com',
        email_confirmed_at=datetime.datetime.utcnow(),
        password=user_manager.hash_password('Password1'),
    )
    db.session.add(user)
    db.session.commit()

# Create 'admin@example.com' user with 'Admin' and 'Agent' roles
if not User.query.filter(User.email == 'admin@example.com').first():
    user = User(
        username='admin',
        email='admin@example.com',
        email_confirmed_at=datetime.datetime.utcnow(),
        password=user_manager.hash_password('Password1'),
    )
    user.roles.append(Role(name='Admin'))
    user.roles.append(Role(name='Agent'))
    db.session.add(user)
    db.session.commit()


from boonai.project.api.datasets import data_blueprint
from boonai.project.api.machine_learning.models import models_blueprint
from boonai.project.api.machine_learning.algorithms import algorithms_blueprint

from boonai.project.api.samples import al_blueprint
from boonai.project.api.storage import storage_blueprint
from boonai.project.api.storage_adapter import storage_adapter_blueprint

app.register_blueprint(data_blueprint, url_prefix='/api')
app.register_blueprint(algorithms_blueprint, url_prefix='/api')
app.register_blueprint(models_blueprint, url_prefix='/api')
app.register_blueprint(al_blueprint, url_prefix='/api')
app.register_blueprint(storage_blueprint, url_prefix='/api')
app.register_blueprint(storage_adapter_blueprint, url_prefix='/api')

from boonai.project.site.routes import mod as site_mod
from boonai.project.site.datasets import mod as datasets_mod
from boonai.project.site.machine_learning import mod as ml_mod
from boonai.project.site.dataprep import mod as dataprep_mod
app.register_blueprint(site_mod, url_prefix='/')
app.register_blueprint(datasets_mod, url_prefix='/datasets')
app.register_blueprint(ml_mod, url_prefix='/ml')
app.register_blueprint(dataprep_mod, url_prefix='/datasets')