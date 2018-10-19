from typing import Dict, List, Tuple

import requests
from keras.layers import (LSTM, Activation, Conv1D, Dense, Dropout, Flatten,
                          Input, MaxPooling1D)
from keras.layers.embeddings import Embedding
# Keras
from keras.models import Model, Sequential
from keras.optimizers import RMSprop
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import Tokenizer
from keras.wrappers.scikit_learn import KerasClassifier
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline


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

class Preparation(BaseEstimator, TransformerMixin):
    # TODO: Make this dynamic, it should use max len from the training set, the longest sentence there
    VOCAB_SIZE = 1000
    MAXLEN = 200
    def fit(self, X, y):
        ### Create sequence
        # vocabulary_size = 5000
        self.tokenizer = Tokenizer(num_words=self.VOCAB_SIZE)
        self.tokenizer.fit_on_texts(X)
        #
        # sequences = self.tokenizer.texts_to_sequences(X)
        # self.maxlen = max(len(s) for s in sequences) + 20
        # TODO: Or just hard code to 200 or so
        return self

    def transform(self, X):
        # We do the custom pipline class because of this padding
        # TODO: Maybe this can be done differently
        sequences = self.tokenizer.texts_to_sequences(X)
        return pad_sequences(sequences, maxlen=self.MAXLEN)



def get_rnn_model():
    VOCAB_SIZE = 1000
    MAXLEN = 200
    max_length = MAXLEN
    vocab_size = VOCAB_SIZE
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


def train_lstm(X, y):
    pipeline = make_pipeline(
        Preparation(),
        KerasClassifier(build_fn=get_rnn_model, epochs=1, verbose=2)
    )
    pipeline.fit(X, y)

    return pipeline
