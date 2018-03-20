from keras.layers import Dense, Dropout, Flatten, Input, MaxPooling1D, Convolution1D, Embedding
from keras.models import load_model
from keras.layers.merge import Concatenate
from keras.models import Model
from keras import models
from keras import layers


class CnnModel:
    """adapted from alexander-rakhlin's code, change the binary classification to multiple classes classification"""

    def __init__(self, vocab_size, label_size, sequence_length=200, embedding_dim=300, filter_sizes=(3, 8),
                 num_filters=10,
                 dropout_prob=(0.5, 0.8),
                 hidden_dims=50,
                 batch_size=60,
                 num_epochs=30,
                 model_file='models/trained.h5'
                 ):
        self.num_epochs = num_epochs
        self.batch_size = batch_size
        input_shape = (sequence_length, embedding_dim)
        model_input = Input(shape=(200, 300))

        z = Dropout(dropout_prob[0])(model_input)

        # Convolutional block
        conv_blocks = []
        for sz in filter_sizes:
            conv = Convolution1D(filters=num_filters,
                                 kernel_size=sz,
                                 padding="valid",
                                 activation="relu",
                                 strides=1)(z)
            conv = MaxPooling1D(pool_size=2)(conv)
            conv = Flatten()(conv)
            conv_blocks.append(conv)
        z = Concatenate()(conv_blocks) if len(conv_blocks) > 1 else conv_blocks[0]

        z = Dropout(dropout_prob[1])(z)
        z = Dense(hidden_dims, activation="relu")(z)
        model_output = Dense(label_size, activation="softmax")(z)

        model = Model(model_input, model_output)
        # model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])

        model.compile(optimizer='rmsprop',
                      loss='categorical_crossentropy',
                      metrics=['accuracy'])
        # model = models.Sequential()
        # # model.add(Input(shape=input_shape))
        # model.add(Embedding(vocab_size, embedding_dim, input_length=sequence_length, name="embedding"))
        # model.add(Dropout(dropout_prob[0]))
        # for sz in filter_sizes:
        # 	model.add(Convolution1D(filters=num_filters,
        # 							kernel_size=sz,
        # 							padding="valid",
        # 							activation="relu",
        # 							strides=1))
        # 	model.add(MaxPooling1D(pool_size=2))
        # 	model.add(Flatten())
        # model.add(Concatenate())
        # model.add(Dropout(dropout_prob[1]))
        # model.add(Dense(hidden_dims, activation="relu"))
        # model.add(Dense(label_size, activation='softmax'))

        # for multiple classes training
        # self.model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

        self.model = model

    def fit(self, x_train, y_train, batch_size=None, num_epochs=None):
        if num_epochs is None:
            num_epochs = self.num_epochs
        if batch_size is None:
            batch_size = self.batch_size
        self.model.fit(x_train, y_train, batch_size=batch_size, epochs=num_epochs, verbose=2)

    def evaluate(self, x_test, y_test, batch_size=None, num_epochs=None):
        if num_epochs is None:
            num_epochs = self.num_epochs
        if batch_size is None:
            batch_size = self.batch_size
        outs = self.model.evaluate(x_test, y_test, batch_size=batch_size, verbose=1)
        return outs

    def saveModel(self, model_file=None):
        if model_file is None:
            model_file = self.model_file
        self.model.save(model_file, overwrite=True, include_optimizer=True)

    def loadTrainedModel(self, model_file=None):
        self.model_file = model_file
        self.model = load_model(model_file)

    def predict(self, x):
        return self.model.predict(x, steps=1)
