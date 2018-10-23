from boonai.project.api.machine_learning.definitions.Algorithm import Algorithm

from typing import List

# Keras
from keras import backend
from keras.layers import LSTM, Activation, Dense, Dropout, Input
from keras.layers.embeddings import Embedding
from keras.models import Model, Sequential
from keras.optimizers import RMSprop
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import Tokenizer


#     from gensim.models import Word2Vec
#     w2v_model = Word2Vec.load(w2v_path)
#     embedding_matrix = w2v_model.wv
#

def get_rnn_model(vocab_size, max_length):
    inputs = Input(name='inputs', shape=[max_length])
    layer = Embedding(vocab_size, 32, input_length=max_length)(inputs)
    layer = LSTM(128)(layer)
    layer = Dense(256, name='FC1')(layer)
    layer = Activation('relu')(layer)
    layer = Dropout(0.3)(layer)
    layer = Dense(1, name='out_layer')(layer)
    layer = Activation('sigmoid')(layer)
    model = Model(inputs=inputs, outputs=layer)

    print(model.summary())

    model.compile(
        loss='binary_crossentropy', optimizer=RMSprop(), metrics=['accuracy']
    )
    return model


class LstmAlgorithm(Algorithm):

    name = 'NN LSTM'
    description = 'NN LSTM for NLP'
    creator = 1  # user id?
    tags = ['nlp', 'text', 'reports']
    groups = ['nlp']

    VOCAB_SIZE = 200
    MAXLEN = 600
    EPOCHS = 5

    tokenizer = None
    model = None

    def __init_subclass__(cls, **kwargs):
        backend.clear_session()

    def train(self, x: List[str], y: List[int]):
        self.tokenizer = Tokenizer(num_words=self.VOCAB_SIZE)
        self.tokenizer.fit_on_texts(x)

        sequences = self.tokenizer.texts_to_sequences(x)
        padded_sequences = pad_sequences(sequences, maxlen=self.MAXLEN)

        self.model = get_rnn_model(self.VOCAB_SIZE, self.MAXLEN)
        self.model.fit(padded_sequences, y, epochs=self.EPOCHS, verbose=2)

    def predict(self, x):
        if self.tokenizer is None or self.model is None:
            self.load()
        sequences = self.tokenizer.texts_to_sequences(x)
        padded_sequences = pad_sequences(sequences, maxlen=self.MAXLEN)

        y_proba = self.model.predict(padded_sequences)
        return (y_proba >= 0.5).astype(int)

    def persist(self):
        self._persist_sklearn(self.tokenizer)
        self._persist_keras(self.model)

    def load(self):
        self.tokenizer = self._load_sklearn()
        self.model = self._load_keras()
