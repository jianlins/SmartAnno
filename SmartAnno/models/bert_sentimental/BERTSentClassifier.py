from collections import Counter

import bert
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from bert import optimization
from bert import run_classifier
from bert import tokenization
import joblib
from sklearn.model_selection import train_test_split

# https://colab.research.google.com/github/google-research/bert/blob/master/predicting_movie_reviews_with_bert_on_tf_hub.ipynb#scrollTo=fom_ff20gyy6
# https://tfhub.dev/google/universal-sentence-encoder/2
from SmartAnno.gui.Workflow import logMsg
from SmartAnno.models.BaseClassifier import BaseClassifier, InTraining, ReadyTrained

not_met_suffix = '_not_met'


class BERTSentimentalClassifier(BaseClassifier):
    # optional paramters with default values here (will be overwritten by ___init__'s **kwargs)
    # These parameters will be shown in GUI ask for users' configuration
    BATCH_SIZE = 32
    cv = 2
    LEARNING_RATE = 2e-5
    NUM_TRAIN_EPOCHS = 3.0
    # Warmup is a period of time where hte learning rate
    # is small and gradually increases--usually helps training.
    WARMUP_PROPORTION = 0.1
    test_size = 0.3
    # Model configs
    SAVE_CHECKPOINTS_STEPS = 500
    SAVE_SUMMARY_STEPS = 100
    MAX_SEQ_LENGTH = 128
    random_state = 777
    OUTPUT_DIR = 'models/saved/bert_sentimental'

    def __init__(self, task_name='default_task', pipeline=None, params=None, model_file=None, **kwargs):
        self.pipeline = pipeline
        self.BERT_MODEL_HUB = "https://tfhub.dev/google/bert_uncased_L-12_H-768_A-12/1"
        self.tokenizer = self.create_tokenizer_from_hub_module()
        super().__init__(task_name, pipeline, params, model_file, **kwargs)

        pass

    def create_tokenizer_from_hub_module(self):
        """Get the vocab file and casing info from the Hub module."""
        with tf.Graph().as_default():
            bert_module = hub.Module(self.BERT_MODEL_HUB)
            tokenization_info = bert_module(signature="tokenization_info", as_dict=True)
            with tf.Session() as sess:
                vocab_file, do_lower_case = sess.run([tokenization_info["vocab_file"],
                                                      tokenization_info["do_lower_case"]])

        return bert.tokenization.FullTokenizer(
            vocab_file=vocab_file, do_lower_case=do_lower_case)

    def defineModel(self):
        self.bert_module = hub.Module(
            self.BERT_MODEL_HUB,
            trainable=True)

    def setup_model(self, label_list: list):
        if self.pipeline is None:
            # Specify outpit directory and number of checkpoint steps to save
            run_config = tf.estimator.RunConfig(
                model_dir=self.OUTPUT_DIR,
                save_summary_steps=self.SAVE_SUMMARY_STEPS,
                save_checkpoints_steps=self.SAVE_CHECKPOINTS_STEPS)
            model_fn = self.model_fn_builder(
                num_labels=len(label_list),
                learning_rate=self.LEARNING_RATE,
                num_train_steps=self.num_train_steps,
                num_warmup_steps=self.num_warmup_steps)
            estimator = tf.estimator.Estimator(
                model_fn=model_fn,
                config=run_config,
                params={"batch_size": self.BATCH_SIZE})
        return estimator

    def create_model(self, is_predicting, input_ids, input_mask, segment_ids, labels,
                     num_labels):
        """Creates a classification model."""

        bert_module = self.bert_module
        bert_inputs = dict(
            input_ids=input_ids,
            input_mask=input_mask,
            segment_ids=segment_ids)
        bert_outputs = bert_module(
            inputs=bert_inputs,
            signature="tokens",
            as_dict=True)

        # Use "pooled_output" for classification tasks on an entire sentence.
        # Use "sequence_outputs" for token-level output.
        output_layer = bert_outputs["pooled_output"]

        hidden_size = output_layer.shape[-1].value

        # Create our own layer to tune for politeness data.
        output_weights = tf.get_variable(
            "output_weights", [num_labels, hidden_size],
            initializer=tf.truncated_normal_initializer(stddev=0.02))

        output_bias = tf.get_variable(
            "output_bias", [num_labels], initializer=tf.zeros_initializer())

        with tf.variable_scope("loss"):
            # Dropout helps prevent overfitting
            output_layer = tf.nn.dropout(output_layer, keep_prob=0.9)

            logits = tf.matmul(output_layer, output_weights, transpose_b=True)
            logits = tf.nn.bias_add(logits, output_bias)
            log_probs = tf.nn.log_softmax(logits, axis=-1)

            # Convert labels into one-hot encoding
            one_hot_labels = tf.one_hot(labels, depth=num_labels, dtype=tf.float32)

            predicted_labels = tf.squeeze(tf.argmax(log_probs, axis=-1, output_type=tf.int32))
            # If we're predicting, we want predicted labels and the probabiltiies.
            if is_predicting:
                return (predicted_labels, log_probs)

            # If we're train/eval, compute loss between predicted and actual label
            per_example_loss = -tf.reduce_sum(one_hot_labels * log_probs, axis=-1)
            loss = tf.reduce_mean(per_example_loss)
        return (loss, predicted_labels, log_probs)

    # model_fn_builder actually creates our model function
    # using the passed parameters for num_labels, learning_rate, etc.
    def model_fn_builder(self, num_labels, learning_rate, num_train_steps,
                         num_warmup_steps):
        """Returns `model_fn` closure for TPUEstimator."""

        def model_fn(features, labels, mode, params):  # pylint: disable=unused-argument
            """The `model_fn` for TPUEstimator."""

            input_ids = features["input_ids"]
            input_mask = features["input_mask"]
            segment_ids = features["segment_ids"]
            label_ids = features["label_ids"]

            is_predicting = (mode == tf.estimator.ModeKeys.PREDICT)

            # TRAIN and EVAL
            if not is_predicting:

                (loss, predicted_labels, log_probs) = self.create_model(
                    is_predicting, input_ids, input_mask, segment_ids, label_ids, num_labels)

                train_op = bert.optimization.create_optimizer(
                    loss, learning_rate, num_train_steps, num_warmup_steps, use_tpu=False)

                # Calculate evaluation metrics.
                def metric_fn(label_ids, predicted_labels):
                    accuracy = tf.metrics.accuracy(label_ids, predicted_labels)
                    f1_score = tf.contrib.metrics.f1_score(
                        label_ids,
                        predicted_labels)
                    auc = tf.metrics.auc(
                        label_ids,
                        predicted_labels)
                    recall = tf.metrics.recall(
                        label_ids,
                        predicted_labels)
                    precision = tf.metrics.precision(
                        label_ids,
                        predicted_labels)
                    true_pos = tf.metrics.true_positives(
                        label_ids,
                        predicted_labels)
                    true_neg = tf.metrics.true_negatives(
                        label_ids,
                        predicted_labels)
                    false_pos = tf.metrics.false_positives(
                        label_ids,
                        predicted_labels)
                    false_neg = tf.metrics.false_negatives(
                        label_ids,
                        predicted_labels)
                    return {
                        "eval_accuracy": accuracy,
                        "f1_score": f1_score,
                        "auc": auc,
                        "precision": precision,
                        "recall": recall,
                        "true_positives": true_pos,
                        "true_negatives": true_neg,
                        "false_positives": false_pos,
                        "false_negatives": false_neg
                    }

                eval_metrics = metric_fn(label_ids, predicted_labels)

                if mode == tf.estimator.ModeKeys.TRAIN:
                    return tf.estimator.EstimatorSpec(mode=mode,
                                                      loss=loss,
                                                      train_op=train_op)
                else:
                    return tf.estimator.EstimatorSpec(mode=mode,
                                                      loss=loss,
                                                      eval_metric_ops=eval_metrics)
            else:
                (predicted_labels, log_probs) = self.create_model(
                    is_predicting, input_ids, input_mask, segment_ids, label_ids, num_labels)

                predictions = {
                    'probabilities': log_probs,
                    'labels': predicted_labels
                }
                return tf.estimator.EstimatorSpec(mode, predictions=predictions)

        # Return the actual model function in the closure
        return model_fn

    def gen_feature(self, x: list, y: list, is_training=False):
        inputExamples = [bert.run_classifier.InputExample(guid=None, text_a=x[i], text_b=None, label=y[i]) for i in
                         range(0, len(x))]
        input_features = bert.run_classifier.convert_examples_to_features(inputExamples, y, self.MAX_SEQ_LENGTH,
                                                                          self.tokenizer)
        input_fn = bert.run_classifier.input_fn_builder(features=input_features, seq_length=self.MAX_SEQ_LENGTH,
                                                        is_training=is_training, drop_remainder=False)
        self.num_train_steps = int(len(input_features) / self.BATCH_SIZE * self.NUM_TRAIN_EPOCHS)
        self.num_warmup_steps = int(self.num_train_steps * self.WARMUP_PROPORTION)
        return input_fn

    def train(self, x: list, y: list):
        BERTSentimentalClassifier.status = InTraining
        logMsg('split data...')
        X_train, X_test, y_train, y_test = train_test_split(x, y,
                                                            test_size=self.test_size,
                                                            random_state=BERTSentimentalClassifier.random_state)

        # make sure there is enough data (overall data and data for each class) to train
        stats = Counter(y_train)
        for classname, count in stats.items():
            if count < self.cv:
                logMsg(
                    'The whole annotated Data does not have enoguh examples for all classes.  Skipping training for '
                    'class : {}'.format(
                        classname))
                return

        train_classes, train_y_indices = np.unique(y_train, return_inverse=True)
        train_minority_instances = np.min(np.bincount(train_y_indices))
        test_minority_instances = np.min(np.bincount(train_y_indices))
        print('Train minority class instance count : {0}.  Test minority class instance count : {1}'.format(
            train_minority_instances,
            test_minority_instances))
        if train_minority_instances <= self.cv:
            logMsg(
                'TRAIN data does not have enoguh examples (require {} cases) for all classes ({} cases) .  Skipping '
                'training for task : {}'.format(
                    self.cv, train_minority_instances, classname))
            return

        if test_minority_instances <= self.cv:
            logMsg(
                'TEST data does not have enoguh examples (require {} cases) for all classes ({} cases) .  Skipping '
                'training for task : {}'.format(
                    self.cv, train_minority_instances, classname))
            return

        # start training
        logMsg('training...')

        train_input_fn = self.gen_feature(X_train, y_train, True)
        self.model = self.setup_model(y_train)
        self.model.train(input_fn=train_input_fn, max_steps=self.num_train_steps)

        test_input_fn = self.gen_feature(X_train, y_train, False)
        self.model.evaluate(input_fn=test_input_fn, steps=None)
        # print performances

        BERTSentimentalClassifier.status = ReadyTrained
        pass

    def classify(self, txt):
        output = self.get_predictions([txt])[0]
        return output

    def get_predictions(self, input_sentences):
        labels = ["Negative", "Positive"]
        predict_input_fn = self.gen_feature(input_sentences, [0] * len(input_sentences))
        predictions = self.model.predict(predict_input_fn)
        return [labels[prediction['labels']] for prediction in
                predictions]

    def saveModel(self):
        """will be automatically saved when user click complete"""
        joblib.dump(self.model, self.model_file)
        pass

    def loadModel(self):
        """will be automatically load when initiate the classifier if self.model_file exists."""
        model = joblib.load(self.model_file)
        BaseClassifier.status = ReadyTrained
        return model
