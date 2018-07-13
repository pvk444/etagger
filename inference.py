from __future__ import print_function
import tensorflow as tf
import numpy as np
from config import Config
from model import Model
from eval  import Eval
from input import *
import sys
import argparse

def inference_bulk(config):
    '''
    inference for test file
    '''

    # Build input data
    test_file = 'data/test.txt'
    test_data = Input(test_file, config)
    print('max_sentence_length = %d' % test_data.max_sentence_length)
    print('loading input data ... done')

    # Create model
    model = Model(config)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        saver = tf.train.Saver()
        saver.restore(sess, config.restore)
        print('model restored')
        feed_dict = {model.input_data_word_ids: test_data.sentence_word_ids,
                     model.input_data_etc: test_data.sentence_etc,
                     model.output_data: test_data.sentence_tag}
        pred, length, test_loss = sess.run([model.prediction, model.length, model.loss], feed_dict=feed_dict)
        print('test score:')
        fscore = Eval.compute_f1(config.class_size, pred, test_data.sentence_tag, length)
        print('total fscore:')
        print(fscore)

def inference_bucket(config):
    '''
    inference for bucket
    '''

    # Create model
    model = Model(config)

    # Restore model
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    saver.restore(sess, config.restore)
    sys.stderr.write('model restored' +'\n')

    bucket = []
    while 1:
        try: line = sys.stdin.readline()
        except KeyboardInterrupt: break
        if not line: break
        line = line.strip()
        if not line and len(bucket) >= 1:
            # Build input data
            inp = Input(bucket, config)
            feed_dict = {model.input_data_word_ids: inp.sentence_word_ids,
                         model.input_data_etc: inp.sentence_etc,
                         model.output_data: inp.sentence_tag}
            pred, length, loss = sess.run([model.prediction, model.length, model.loss], feed_dict=feed_dict)
            labels = Input.pred_to_label(pred[0], length[0])
            for i in range(len(bucket)):
                out = bucket[i] + ' ' + labels[i]
                sys.stdout.write(out + '\n')
            sys.stdout.write('\n')
            bucket = []
        if line : bucket.append(line)
    if len(bucket) != 0:
        # Build input data
        inp = Input(bucket, config)
        feed_dict = {model.input_data_word_ids: inp.sentence_word_ids,
                     model.input_data_etc: inp.sentence_etc,
                     model.output_data: inp.sentence_tag}
        pred, length, loss = sess.run([model.prediction, model.length, model.loss], feed_dict=feed_dict)
        labels = Input.pred_to_label(pred[0], length[0])
        for i in range(len(bucket)):
            out = bucket[i] + ' ' + labels[i]
            sys.stdout.write(out + '\n')
        sys.stdout.write('\n')

    sess.close()

def inference_line(config):
    '''
    inference for raw string
    '''
    def build_bucket(nlp, line):
        bucket = []
        uline = line.decode('utf-8','ignore') # unicode
        doc = nlp(uline)
        for token in doc:
            temp = []
            '''
            print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
                  token.shape_, token.is_alpha, token.is_stop)
            '''
            temp.append(token.text)
            temp.append(token.tag_)
            temp.append('O')  # no chunking info
            temp.append('O')  # label
            utemp = ' '.join(temp)
            bucket.append(utemp.encode('utf-8'))
        return bucket

    import spacy
    nlp = spacy.load('en')

    # Create model
    model = Model(config)

    # Restore model
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())
    saver = tf.train.Saver()
    saver.restore(sess, config.restore)
    sys.stderr.write('model restored' +'\n')

    while 1:
        try: line = sys.stdin.readline()
        except KeyboardInterrupt: break
        if not line: break
        line = line.strip()
        if not line: continue
        # Create bucket
        try: bucket = build_bucket(nlp, line)
        except Exception as e:
            sys.stderr.write(str(e) +'\n')
            continue
        # Build input data
        inp = Input(bucket, config)
        feed_dict = {model.input_data_word_ids: inp.sentence_word_ids,
                     model.input_data_etc: inp.sentence_etc,
                     model.output_data: inp.sentence_tag}
        pred, length, loss = sess.run([model.prediction, model.length, model.loss], feed_dict=feed_dict)
        labels = Input.pred_to_label(pred[0], length[0])
        for i in range(len(bucket)):
            out = bucket[i] + ' ' + labels[i]
            sys.stdout.write(out + '\n')
        sys.stdout.write('\n')

    sess.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--emb_path', type=str, help='path to word embedding vector(.pkl)', required=True)
    parser.add_argument('--emb_dim', type=int, help='dimension of word embedding vector', required=True)
    parser.add_argument('--sentence_length', type=int, help='max sentence length', required=True)
    parser.add_argument('--class_size', type=int, help='number of classes', required=True)
    parser.add_argument('--restore', type=str, help='path to saved model(ex, ./checkpoint/model_max.ckpt)', required=True)
    parser.add_argument('--mode', type=str, default='bulk', help='bulk, bucket, line')

    args = parser.parse_args()
    config = Config(args, is_train=0)
    if args.mode == 'bulk':   inference_bulk(config)
    if args.mode == 'bucket': inference_bucket(config)
    if args.mode == 'line':   inference_line(config)
