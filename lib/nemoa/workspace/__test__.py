# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa

from nemoa.common.unittest import TestSuite as NmTestSuite

class TestSuite(NmTestSuite):

    def test_workspace_open(self):
        nemoa.open('testsuite')
        test = nemoa.get('workspace') == 'testsuite'
        self.assertTrue(test)