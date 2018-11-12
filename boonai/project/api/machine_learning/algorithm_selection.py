def create_algorithm_dict(uid, func, name, desc, creator, other):
    return {
        'id': uid,
        'func': func,
        'name': name,
        'description': desc,
        'creator': creator,
        'other': other
    }


from boonai.project.api.machine_learning.definitions.nlp.GridSearchRfcAlgorithm import \
    GridSearchRfcAlgorithm
from boonai.project.api.machine_learning.definitions.nlp.GridSearchSvcAlgorithm import \
    GridSearchSvcAlgorithm
from boonai.project.api.machine_learning.definitions.nlp.RfcAlgorithm import \
    RfcAlgorithm
from boonai.project.api.machine_learning.definitions.nlp.SvcAlgorithm import \
    SvcAlgorithm

from boonai.project.api.machine_learning.definitions.nlp.LstmAlgorithm import \
    LstmAlgorithm

from boonai.project.api.machine_learning.definitions.nlp.CnnLstmAlgorithm import \
    CnnLstmAlgorithm

from boonai.project.api.machine_learning.definitions.nlp.LstmEmbedAlgorithm import \
    LstmEmbedAlgorithm

from boonai.project.api.machine_learning.definitions.nlp.SvmProbaAlgorithm import \
    SvmProbaAlgorithm

from boonai.project.api.machine_learning.definitions.nlp.RfcProbaAlgorithm import \
    RfcProbaAlgorithm


algorithm_dict = {
    1: SvcAlgorithm,
    2: RfcAlgorithm,
    3: GridSearchSvcAlgorithm,
    4: GridSearchRfcAlgorithm,
    5: LstmEmbedAlgorithm,
    6: CnnLstmAlgorithm,
    7: SvmProbaAlgorithm,
    8: RfcProbaAlgorithm,
    9: LstmAlgorithm
}


def get_algorithms_info():
    return [
        {
            'id': key,
            'name': algorithm_dict[key].name
        }
        for key in algorithm_dict
    ]


functions_dict = {
    key: algorithm_dict[key]('0.0.0.0:5000/api/v1/storage')
    for key in algorithm_dict
}

algorithms_info = {}
for info in get_algorithms_info():
    uid = info['id']
    algorithms_info[uid] = info
