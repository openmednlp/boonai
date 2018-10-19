import pickle
from abc import ABC, abstractmethod

import h5py
import requests
from keras.models import load_model, save_model

from boonai.project.site import helper as h


class Algorithm(ABC):
    id = None
    name = None
    description = None
    creator = None
    tags = []
    groups = []
    pipeline = None
    storage_adapter_api = None
    resources = {}

    def __init__(self, storage_adapter_api):
        self.storage_adapter_api = storage_adapter_api

    @abstractmethod
    def train(self, x, y):
        return

    @abstractmethod
    def predict(self, x):
        return

    @abstractmethod
    def persist(self):
        return

    @abstractmethod
    def load(self):
        return

    @staticmethod
    def _get_binary(uri):
        # TODO: could use another approach if multiple storage backends are used
        r_json = requests.get(uri).json()
        bin_uri = h.hateoas_get_link(r_json, 'binary')
        return requests.get(bin_uri).content

    def _persist_sklearn(self):
        model_pickle = pickle.dumps(self.pipeline)
        r = requests.post(self.storage_adapter_api, data=model_pickle)
        storage_adapter_uri = h.hateoas_get_link(r.json(), 'self')
        self.resources['sklearn'] = storage_adapter_uri
        return storage_adapter_uri  # TODO: not sure if useful

    def _persist_keras(self, model):
        # Save the model to an in-memory-only h5 file.
        with h5py.File(
                'does not matter',
                driver='core',
                backing_store=False) as h5file:
            save_model(model, h5file)
            h5file.flush()  # Very important! Otherwise you get all zeroes below.
            binary_data = h5file.fid.get_file_image()
        r = requests.post(self.storage_adapter_api, data=binary_data)
        storage_adapter_uri = h.hateoas_get_link(r.json(), 'self')
        self.resources['keras'] = storage_adapter_uri
        return storage_adapter_uri

    def _load_sklearn(self):
        bin = self._get_binary(self.resources['sklearn'])
        return pickle.loads(bin)

    def _load_keras(self):
        bin_uri = self._get_binary(self.resources['keras'])
        return load_model(requests.get(bin_uri).content)
