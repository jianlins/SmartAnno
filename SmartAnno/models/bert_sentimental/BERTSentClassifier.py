import numpy as np
from bert import optimization
from bert import run_classifier
from bert import tokenization

# https://colab.research.google.com/github/google-research/bert/blob/master/predicting_movie_reviews_with_bert_on_tf_hub.ipynb#scrollTo=fom_ff20gyy6
# https://tfhub.dev/google/universal-sentence-encoder/2
from SmartAnno.models.BaseClassifier import BaseClassifier, InTraining, ReadyTrained, NotTrained

not_met_suffix = '_not_met'

import os

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
# The GPU id to use, usually either "0" or "1"
# check the ids using command nvidia-smi in terminal
os.environ["CUDA_VISIBLE_DEVICES"] = "3"
# -

import tensorflow as tf
import tensorflow_hub as hub
from datetime import datetime

import bert
from bert import run_classifier

MAX_SEQ_LENGTH = 128

# These hyperparameters are copied from this colab notebook (https://colab.sandbox.google.com/github/tensorflow/tpu/blob/master/tools/colab/bert_finetuning_with_cloud_tpus.ipynb)
BATCH_SIZE = 32
LEARNING_RATE = 2e-5
NUM_TRAIN_EPOCHS = 3.0
# Warmup is a period of time where hte learning rate
# is small and gradually increases--usually helps training.
WARMUP_PROPORTION = 0.1
# Model configs
SAVE_CHECKPOINTS_STEPS = 500
SAVE_SUMMARY_STEPS = 100
BERT_MODEL_HUB = "https://tfhub.dev/google/bert_uncased_L-12_H-768_A-12/1"


class BERTSentClassifier(BaseClassifier):

    def __init__(self, task_name='default_task', model_file=None, **kwargs):
        BERTSentClassifier.status = NotTrained
        self.task_name = task_name
        self.saved_models_root = 'models/saved/'
        if model_file is None:
            model_file = 'bert_sent_' + task_name
        self.model_file = os.path.join(self.saved_models_root, model_file)
        self.label_list = []
        self.estimator = None
        # @markdown Whether or not to clear/delete the directory and create a new one
        DO_DELETE = False  # @param {type:"boolean"}
        if DO_DELETE:
            try:
                tf.gfile.DeleteRecursively(model_file)
            except:
                # Doesn't matter if the directory didn't exist
                pass
        tf.gfile.MakeDirs(model_file)
        print('***** Model output directory: {} *****'.format(model_file))
        self.tokenizer = self.create_tokenizer_from_hub_module()
        pass

    def create_tokenizer_from_hub_module(self):
        """Get the vocab file and casing info from the Hub module."""
        with tf.Graph().as_default():
            bert_module = hub.Module(BERT_MODEL_HUB)
            tokenization_info = bert_module(signature="tokenization_info", as_dict=True)
            with tf.Session() as sess:
                vocab_file, do_lower_case = sess.run([tokenization_info["vocab_file"],
                                                      tokenization_info["do_lower_case"]])

        return bert.tokenization.FullTokenizer(
            vocab_file=vocab_file, do_lower_case=do_lower_case)

    def train(self, x: np.ndarray, y: np.ndarray):
        BERTSentClassifier.status = InTraining
        inputExamples = [bert.run_classifier.InputExample(guid=None, text_a=text, text_b=None, label=label) for
                         (text, label) in zip(x, y)]
        self.label_list = np.unique(y)
        print('List labels: ', self.label_list)
        # Convert our train and test features to InputFeatures that BERT understands.
        input_features = bert.run_classifier.convert_examples_to_features(inputExamples, self.label_list,
                                                                          MAX_SEQ_LENGTH,
                                                                          self.tokenizer)

        input_fn = bert.run_classifier.input_fn_builder(
            features=input_features,
            seq_length=MAX_SEQ_LENGTH,
            is_training=True,
            drop_remainder=False)

        run_config = tf.estimator.RunConfig(
            model_dir=self.model_file,
            save_summary_steps=SAVE_SUMMARY_STEPS,
            save_checkpoints_steps=SAVE_CHECKPOINTS_STEPS)

        num_train_steps = int(len(input_features) / BATCH_SIZE * NUM_TRAIN_EPOCHS)
        num_warmup_steps = int(num_train_steps * WARMUP_PROPORTION)

        model_fn = self.model_fn_builder(
            num_labels=len(self.label_list),
            learning_rate=LEARNING_RATE,
            num_train_steps=num_train_steps,
            num_warmup_steps=num_warmup_steps)

        self.estimator = tf.estimator.Estimator(
            model_fn=model_fn,
            config=run_config,
            params={"batch_size": BATCH_SIZE})

        print(f'Beginning Training!')
        current_time = datetime.now()
        self.estimator.train(input_fn=input_fn, max_steps=num_train_steps)
        print("Training took time ", datetime.now() - current_time)
        BERTSentClassifier.status = ReadyTrained
        pass

    def predict(self, input_sentences: list):
        input_examples = [run_classifier.InputExample(guid="", text_a=x, text_b=None, label=self.label_list[0]) for x in
                          input_sentences]  # here, "" is just a dummy label
        input_features = run_classifier.convert_examples_to_features(input_examples, self.label_list, MAX_SEQ_LENGTH,
                                                                     self.tokenizer)
        predict_input_fn = run_classifier.input_fn_builder(features=input_features, seq_length=MAX_SEQ_LENGTH,
                                                           is_training=False, drop_remainder=False)
        predictions = self.estimator.predict(predict_input_fn)
        return [p for p in predictions]

    def create_model(self, is_predicting, input_ids, input_mask, segment_ids, labels,
                     num_labels):
        """Creates a classification model."""

        bert_module = hub.Module(
            BERT_MODEL_HUB,
            trainable=True)
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

    def classify(self, txt):
        # tensorflow v1.13 estimator doesn't work well with single input
        predicts = self.predict([txt, ''])
        return self.label_list[predicts[0]['labels']]

    pass
