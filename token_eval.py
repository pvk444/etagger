from __future__ import print_function
import sys
import argparse
import numpy as np

class TokenEval:
    def __init__(self):
        self.cls = {}
        self.tp = {}
        self.fp = {}
        self.fn = {}
        self.precision = {}
        self.recall = {}
        self.fscore = {}

    def __eval_bucket(self, bucket):
        for line in bucket:
            tokens = line.split()
            size = len(tokens)
            assert(size == 5)
            w = tokens[0]
            pos = tokens[1]
            chunk = tokens[2]
            tag = tokens[3]
            pred = tokens[4]
            if pred not in self.tp: self.tp[pred] = 0
            if tag not in self.tp:  self.tp[tag] = 0
            if pred not in self.fp: self.fp[pred] = 0
            if tag not in self.fp:  self.fp[tag] = 0
            if pred not in self.fn: self.fn[pred] = 0
            if tag not in self.fn:  self.fn[tag] = 0
            if tag == pred:
                self.tp[pred] += 1
            else:
                self.fp[pred] += 1
                self.fn[tag] += 1
            self.cls[pred] = None
            self.cls[tag] = None

    def eval(self):
        """Compute micro precision, recall, fscore given file
        """
        bucket = []
        while 1:
            try: line = sys.stdin.readline()
            except KeyboardInterrupt: break
            if not line: break
            line = line.strip()
            if not line and len(bucket) >= 1:
                self.__eval_bucket(bucket)
                bucket = []
            if line : bucket.append(line)
        if len(bucket) != 0:
            self.__eval_bucket(bucket)

        # in_class vs out_class
        in_class  = 'I'
        out_classes = ['O', 'X']
        self.tp[in_class] = 0
        self.fp[in_class] = 0
        self.fn[in_class] = 0
        for c, _ in self.cls.items():
            if c not in out_classes:
                self.tp[in_class] += self.tp[c]
                self.fp[in_class] += self.fp[c]
                self.fn[in_class] += self.fn[c]
        self.cls[in_class] = None

        print(self.tp)
        print(self.fp)
        print(self.fn)

        for c, _ in self.cls.items():
            if self.tp[c] + self.fp[c] != 0:
                self.precision[c] = self.tp[c]*1.0 / (self.tp[c] + self.fp[c])
            else:
                self.precision[c] = 0
            if self.tp[c] + self.fn[c] != 0:
                self.recall[c] = self.tp[c]*1.0 / (self.tp[c] + self.fn[c])
            else:
                self.recall[c] = 0
            if self.precision[c] + self.recall[c] != 0:
                self.fscore[c] = 2.0*self.precision[c]*self.recall[c] / (self.precision[c] + self.recall[c])
            else:
                self.fscore[c] = 0

        print('')
        print('precision:')
        for c, _ in self.precision.items():
            print(c + ',' + str(self.precision[c]))
        print('')
        print('recall:')
        for c, _ in self.recall.items():
            print(c + ',' + str(self.recall[c]))
        print('')
        print('fscore:')
        for c, _ in self.fscore.items():
            print(c + ',' + str(self.fscore[c]))
        print('')
        print('total fscore:')
        print(self.fscore[in_class])

    @staticmethod
    def compute_f1(class_size, prediction, target, length):
        """Compute micro F1 measure given prediction and target
        """
        tp = np.array([0] * (class_size + 1))
        fp = np.array([0] * (class_size + 1))
        fn = np.array([0] * (class_size + 1))
        target = np.argmax(target, 2)
        prediction = np.argmax(prediction, 2)
        for i in range(len(target)):
            for j in range(length[i]):
                if target[i, j] == prediction[i, j]:
                    tp[prediction[i, j]] += 1
                else:
                    fp[prediction[i, j]] += 1
                    fn[target[i, j]] += 1
        out_of_classes = [0, 1] # SEE embvec.oot_tid, embvec.xot_tid
        for i in range(class_size):
            if i not in out_of_classes:
                tp[class_size] += tp[i]
                fp[class_size] += fp[i]
                fn[class_size] += fn[i]
        precision = []
        recall = []
        fscore = []
        for i in range(class_size + 1):
            precision.append(tp[i] * 1.0 / (tp[i] + fp[i]))
            recall.append(tp[i] * 1.0 / (tp[i] + fn[i]))
            fscore.append(2.0 * precision[i] * recall[i] / (precision[i] + recall[i]))
        print('precision, recall, fscore')
        print(precision)
        print(recall)
        print(fscore)
        return fscore[class_size]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    ev = TokenEval()
    ev.eval()
