from flask_sqlalchemy import SQLAlchemy
from flask_user import UserMixin
from itsdangerous import BadSignature, SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')

    email = db.Column(db.String(255))
    email_confirmed_at = db.Column(db.DateTime())

    # User information
    first_name = db.Column(db.String(100), nullable=False, server_default='')
    last_name = db.Column(db.String(100), nullable=False, server_default='')

    # Define the relationships
    roles = db.relationship('Role', secondary='user_role')
    datasets = db.relationship('Dataset', secondary='user_dataset')
    groups = db.relationship('Group', secondary='user_group')

    def generate_auth_token(self, expiration = 600):
        s = Serializer(db.app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(db.app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user


class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(50), nullable=False)


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(50))


class Dataset(db.Model):
    __tablename__ = 'dataset'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(512))
    train = db.Column(db.Boolean())
    test = db.Column(db.Boolean())
    label = db.Column(db.Boolean())
    project_id = db.Column(db.Integer())
    user_id = db.Column(db.Integer())
    file_id = db.Column(db.Integer())
    storage_adapter_uri = db.Column(db.String(512)) # db.Integer(), db.ForeignKey('storage_adapter.id'), onupdate='CASCADE')
    binary_uri = db.Column(db.String(512))


class UserRole(db.Model):
    __tablename__ = 'user_role'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))


class UserDataset(db.Model):
    __tablename__ = 'user_dataset'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    dataset_id = db.Column(db.Integer(), db.ForeignKey('dataset.id', ondelete='CASCADE'))


class UserDatasets(db.Model):
    __tablename__ = 'user_group'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    group_id = db.Column(db.Integer(), db.ForeignKey('group.id', ondelete='CASCADE'))


class TrainedModel(db.Model):
    __tablename__ = 'trained_model'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(1024))
    project_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    algorithm_id = db.Column(db.Integer)
    dataset_id = db.Column(
        db.Integer(),
        db.ForeignKey('dataset.id', ondelete='CASCADE')
    )
    resources = db.relationship("ModelResource")


class ModelResource(db.Model):
    __tablename__ = 'model_resource'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    uri = db.Column(db.String(1024))
    # bin_uri = db.Column(db.String(1024))
    trained_model_id = db.Column(db.Integer, db.ForeignKey('trained_model.id'))
    trained_model = db.relationship("TrainedModel", back_populates='resources')


class StorageAdapter(db.Model):
    __tablename__ = 'storage_adapter'
    id = db.Column(db.Integer, primary_key=True)
    uri = db.Column(db.String(1024))


# class ModelStorageAdapter(db.Model):
#     __tablename__ = 'model_storage_adapter'
#     id = db.Column(db.Integer, primary_key=True)
#     key = db.Column(db.String(64))
#     trained_model_id = db.Column(
#         db.Integer(),
#         db.ForeignKey('trained_model.id', ondelete='CASCADE')
#     )
#     storage_adapter__id = db.Column(
#         db.Integer(),
#         db.ForeignKey('storage_adapter.id', ondelete='CASCADE')
#     )


class Storage(db.Model):
    __tablename__ = 'storage'
    id = db.Column(db.Integer, primary_key=True)
    binary = db.Column(db.LargeBinary, nullable=False)
