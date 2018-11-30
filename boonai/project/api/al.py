from flask import Blueprint, request
from flask_restful import Api, Resource

from io import StringIO
import numpy as np
import pandas as pd
import requests

from boonai.project.site.helper import url_join

from boonai.project.api.active_learning.inital_selection import get_initial_label_set
from boonai.project.site import helper as h

from boonai.model import Dataset

# TODO move this file level below and rename to ml


def row_to_dict(row):
    return dict(
        (col, getattr(row, col))
        for col
        in row.__table__.columns.keys()
    )


def mark_for_labeling(df, batch_field_name, sample_size):
    unlabeled_df = df[df[batch_field_name] == 0]
    total_unlabeled = len(unlabeled_df)
    sample_size = min(sample_size, total_unlabeled)
    next_batch_value = df[batch_field_name].max() + 1

    # mark a random sample for labeling from the unmarked ones
    labeling_indices = unlabeled_df.sample(sample_size).index
    df.loc[labeling_indices, batch_field_name] = next_batch_value
    return df


class Single(Resource):
    def get(self, dataset_id):
        # Get initial dataset
        dataset_object = Dataset.query.filter_by(id=dataset_id).first()

        input_field = dataset_object.input
        target_field = dataset_object.target
        # label_batch_field = dataset_object.label_batch # TODO: Implement label batch field
        batch_field_name = 'batch'

        storage_uri = dataset_object.binary_uri
        r_storage = requests.get(storage_uri)
        dataset = r_storage.content.decode('utf-8')
        csv = StringIO(dataset)
        df = pd.read_csv(csv)

        sample_size = min(len(df) // 10, 100)

        if batch_field_name not in df.columns:
            sample_size = min(sample_size, len(df))
            result_df = get_initial_label_set(
                df,
                input_field,
                n_clusters=sample_size,
                result_save_path=None,  # TODO: Needs to be temp and removed instantly
                batch_field=batch_field_name
            )
        else:
            unlabeled_rows = df[
                (
                    df[target_field].apply(pd.isnull)
                )
            ]
            marked_unlabeled_rows = df[
                (df[batch_field_name] != 0) &
                (
                    (df[target_field] == '') |
                    (df[target_field].apply(pd.isnull))
                )
            ]
            total_marked_unlabeled = len(marked_unlabeled_rows)

            marked_labels_missing = total_marked_unlabeled != 0
            all_labeled = len(unlabeled_rows) == 0
            if marked_labels_missing or all_labeled:
                result_df = df
            else:
                result_df = mark_for_labeling(df, batch_field_name, sample_size)

        result_csv = result_df.to_csv(index=False, encoding='utf-8').encode('utf-8')
        r = requests.put(
            dataset_object.storage_adapter_uri,
            data=result_csv,
            verify=False
            # headers={'Content-Type': 'application/octet-stream'}
        )

        self_href = url_join(
            request.base_url,
            dataset_id
        )

        return {
            'content': result_df.to_json(),
            'links': [
                {
                    "rel": "self",
                    "href": self_href
                }
            ]
        }

    # def post(self):
    #     pass


al_blueprint = Blueprint('active_learning', __name__)
data_api = Api(al_blueprint, '/v1')
data_api.add_resource(Single, '/datasets/<int:dataset_id>/al')
# TODO: This is API, does not have to be on the dataset

