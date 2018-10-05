# DO NOT CHANGE
# Use instance/application.cfg for local settings

# Flask
DEBUG = True
SECRET_KEY = 'abcdef1234567890a1b2c3d4e5f60987654321fedcba1234'

## SQLAlchemy
SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///sqlite.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

## User
USER_ENABLE_EMAIL = False
USER_ENABLE_USERNAME = True
USER_APP_NAME = 'BoonAI'

# APIs
STORAGE_API = 'http://localhost:5000/api/v1/storage'
DATASETS_API = 'http://localhost:5000/api/v1/datasets'
ALGORITHMS_API = 'http://localhost:5000/api/v1/machine-learning/algorithms'
MODELS_API = 'http://localhost:5000/api/v1/machine-learning/models'

#Dropzone
DROPZONE_UPLOAD_MULTIPLE = True
DROPZONE_ALLOWED_FILE_CUSTOM = True
allowed_file_types = '''
    application/vnd.openxmlformats-officedocument.wordprocessingml.document 
    application/vnd.ms-excel 
    application/vnd.openxmlformats-officedocument.spreadsheetml.sheet  
    application/vnd.ms-excel
    text/csv
    text/plain
    text/x-csv
    '''.split()
DROPZONE_ALLOWED_FILE_TYPE = ','.join(allowed_file_types)
DROPZONE_REDIRECT_VIEW = 'site_dataprep.converter'
DROPZONE_MAX_FILES = 1000
DROPZONE_MAX_FILE_SIZE = 10
