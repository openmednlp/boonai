# DO NOT CHANGE
# Use instance/application.cfg for local settings

# App
DEBUG = True

SECRET_KEY = 'abcdef1234567890a1b2c3d4e5f60987654321fedcba1234'

SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:postgres@localhost/boonai'
SQLALCHEMY_TRACK_MODIFICATIONS = False

USER_ENABLE_EMAIL = False
USER_ENABLE_USERNAME = True

API_URI = 'http://localhost:5000'
STORAGE_API = 'http://localhost:5000/api/v1/storage'
DATASETS_API = 'http://localhost:5000/api/v1/datasets'
ALGORITHMS_API = 'http://localhost:5000/api/v1/algorithms'
MODELS_API = 'http://localhost:5000/api/v1/machine-learning/models'