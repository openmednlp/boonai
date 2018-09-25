from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GridSearchCV


def create_algorithm_dict(uid, func, name, desc, creator, other):
    return {
        'id': uid,
        'func': func,
        'name': name,
        'description': desc,
        'creator': creator,
        'other': other
    }


def train_rfc(X, y):
    pipeline = make_pipeline(
        TfidfVectorizer(),
        RandomForestClassifier()
    )
    pipeline.fit(X, y)
    return pipeline


def train_cv_rfc(X, y):
    pipeline = make_pipeline(
        TfidfVectorizer(),
        RandomForestClassifier()
    )

    parameters = {
        'tfidfvectorizer__use_idf': (True, False),
        'randomforestclassifier__n_estimators': [5, 10, 20],
        'randomforestclassifier__min_samples_split': [2, 3, 5]
    }

    cv = GridSearchCV(pipeline, cv=3, n_jobs=4, param_grid=parameters)
    cv.fit(X, y)
    return cv


def train_svc(X, y):
    pipeline = make_pipeline(
        TfidfVectorizer(),
        LinearSVC()
    )

    pipeline.fit(X, y)
    return pipeline


def train_cv_svc(X, y):
    pipeline = make_pipeline(
        TfidfVectorizer(),
        LinearSVC()
    )
    parameters = {
        'tfidfvectorizer__use_idf': (True, False),
        'linearsvc__C': [1, 10, 100]
    }

    cv = GridSearchCV(pipeline, cv=3, n_jobs=4, param_grid=parameters)
    cv.fit(X, y)
    return cv


def train_cnn_w2v(X, y):
    SEED_NUMBER = 2**10
    RESOURCE_PATH = 'project/api/machine_learning/resources'
    from os import listdir
    from os import path

    filename = [
        f
        for f in listdir(RESOURCE_PATH)
        if path.splitext(f)[1] == '.model'
    ][0]
    w2v_path = path.join(RESOURCE_PATH, filename)

    #Padding missing
    # try doing the whole thing like in the example
    # maybe there is this indexing limitation, where we have to use
    # integer indices, I mean they are just matrix indices, not keys
    # good luck me

    from sklearn.model_selection import train_test_split
    x_train, x_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=.2,
        random_state=SEED_NUMBER
    )
    from gensim.models import Word2Vec
    w2v_model = Word2Vec.load(w2v_path)
    embedding_matrix = w2v_model.wv

    from keras.models import Sequential
    from keras.layers import Dense, Dropout
    from keras.layers import Flatten
    from keras.layers.embeddings import Embedding

    keras_model = Sequential()
    e = Embedding(
        embedding_matrix.vectors.shape[0],
        embedding_matrix.vectors.shape[1],
        weights=[embedding_matrix.vectors],
        input_length=45,
        trainable=False
    )
    keras_model.add(e)
    keras_model.add(Flatten())
    keras_model.add(Dense(256, activation='relu'))
    keras_model.add(Dense(1, activation='sigmoid'))
    keras_model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    keras_model.fit(x_train, y_train, validation_data=(x_val, y_val), epochs=5, batch_size=32, verbose=2)


def train_lstm(X, y):
    # Keras
    from keras.preprocessing.text import Tokenizer
    from keras.preprocessing.sequence import pad_sequences
    from keras.models import Sequential
    from keras.layers import Dense, Flatten, LSTM, Conv1D, MaxPooling1D, Dropout, Activation, Input
    from keras.layers.embeddings import Embedding
    from keras.models import Model
    from keras.wrappers.scikit_learn import KerasClassifier
    from keras.optimizers import RMSprop

    from sklearn.base import BaseEstimator, TransformerMixin

    class Preparation(BaseEstimator, TransformerMixin):
        def fit(self, X, y):
            ### Create sequence
            vocabulary_size = 1000
            self.tokenizer = Tokenizer(num_words=vocabulary_size)
            self.tokenizer.fit_on_texts(X)
            return self

        def transform(self, X):
            sequences = self.tokenizer.texts_to_sequences(X)
            input_length = max(len(s) for s in sequences) + 20
            return pad_sequences(sequences, maxlen=input_length)

    def get_rnn_model():
        max_length = 100
        vocab_size = 5000
        inputs = Input(name='inputs', shape=[max_length])
        layer = Embedding(vocab_size, 32, input_length=max_length)(inputs)
        layer = LSTM(128)(layer)
        layer = Dense(256, name='FC1')(layer)
        layer = Activation('relu')(layer)
        layer = Dropout(0.01)(layer)
        layer = Dense(1, name='out_layer')(layer)
        layer = Activation('sigmoid')(layer)
        model = Model(inputs=inputs, outputs=layer)
        print(model.summary())
        model.compile(
            loss='binary_crossentropy', optimizer=RMSprop(), metrics=['accuracy']
        )
        return model

    kc = KerasClassifier(build_fn=get_rnn_model, epochs=5, verbose=2)
    pipeline = make_pipeline(
        Preparation(),
        kc
    )

    pipeline.fit(X, y)
    return pipeline


def get_algorithms():
    return [
        create_algorithm_dict(
            0,
            train_svc,
            'Default',
            'Basic Linear SVC',
            'admin',
            'Let\'s check what needs to ne added here'),
        create_algorithm_dict(
            1,
            train_rfc,
            'Basic Random Forest',
            'Just a basic RFC',
            'admin',
            'Let\'s check what needs to ne added here'),
        create_algorithm_dict(
            2,
            train_svc,
            'SVC',
            'Basic Linear SVC',
            'admin',
            'Let\'s check what needs to ne added here'),
        create_algorithm_dict(
            3,
            train_cv_rfc,
            'Grid Search RFC',
            'Grid Search optimized RFC',
            'admin',
            'Let\'s check what needs to ne added here'),
        create_algorithm_dict(
            4,
            train_cv_svc,
            'Grid Search Linear SVC',
            'Grid Search optimized Linear SVC',
            'admin',
            'Let\'s check what needs to ne added here'),
        create_algorithm_dict(
            5,
            train_lstm,
            'LSTM',
            'Super magical LSTM',
            'admin',
            'Let\'s check what needs to ne added here'),
    ]


algorithms = get_algorithms()

functions_dict = {
    a['id']: a['func']
    for a in algorithms
}

algorithms_info = {}
for algorithm in algorithms:
    del algorithm['func']
    uid = algorithm['id']
    algorithms_info[uid] = algorithm

