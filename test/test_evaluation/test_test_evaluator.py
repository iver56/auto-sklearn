# -*- encoding: utf-8 -*-
from __future__ import print_function
import copy
import multiprocessing
import os
import shutil
import sys
import unittest

import numpy as np

this_directory = os.path.dirname(__file__)
sys.path.append(this_directory)
from evaluation_util import get_dataset_getters, BaseEvaluatorTest, \
    get_multiclass_classification_datamanager
from autosklearn.constants import *
from autosklearn.evaluation import TestEvaluator
# Otherwise nosetests thinks this is a test to run...
from autosklearn.evaluation import eval_t
from autosklearn.util.pipeline import get_configuration_space

N_TEST_RUNS = 10


class Dummy(object):
    pass


class TestEvaluator_Test(BaseEvaluatorTest):
    _multiprocess_can_split_ = True

    def teardown(self):
        try:
            shutil.rmtree(self.output_dir)
        except Exception:
            pass

        for output_dir in self.output_directories:
            try:
                shutil.rmtree(output_dir)
            except Exception:
                pass

    def test_datasets(self):
        for getter in get_dataset_getters():
            testname = '%s_%s' % (os.path.basename(__file__).
                                  replace('.pyc', '').replace('.py', ''),
                                  getter.__name__)
            with self.subTest(testname):
                D = getter()
                output_directory = os.path.join(os.path.dirname(__file__),
                                                '.%s' % testname)
                self.output_directories.append(output_directory)
                err = np.zeros([N_TEST_RUNS])
                for i in range(N_TEST_RUNS):
                    D_ = copy.deepcopy(D)
                    evaluator = TestEvaluator(D_, output_directory, None)

                    err[i] = evaluator.fit_predict_and_loss()[0]

                    self.assertTrue(np.isfinite(err[i]))


class FunctionsTest(unittest.TestCase):
    def setUp(self):
        self.queue = multiprocessing.Queue()
        self.configuration = get_configuration_space(
            {'task': MULTICLASS_CLASSIFICATION,
             'is_sparse': False}).get_default_configuration()
        self.data = get_multiclass_classification_datamanager()
        self.tmp_dir = os.path.join(os.path.dirname(__file__),
                                    '.test_cv_functions')

    def tearDown(self):
        try:
            shutil.rmtree(self.tmp_dir)
        except Exception:
            pass

    def test_eval_test(self):
        eval_t(self.queue, self.configuration, self.data, self.tmp_dir,
               1, 1, None, True, False, True)
        info = self.queue.get()
        self.assertAlmostEqual(info[1], 0.041666666666666852)
        self.assertEqual(info[2], 1)
        self.assertNotIn('bac_metric', info[3])

    def test_eval_test_all_loss_functions(self):
        eval_t(self.queue, self.configuration, self.data, self.tmp_dir,
               1, 1, None, True, True, True)
        info = self.queue.get()
        self.assertIn('f1_metric: 0.0511508951407;pac_metric: 0.273385527265;'
                      'acc_metric: 0.06;auc_metric: 0.00917546505782;'
                      'bac_metric: 0.0416666666667;duration: ', info[3])
        self.assertAlmostEqual(info[1], 0.041666666666666852)
        self.assertEqual(info[2], 1)

