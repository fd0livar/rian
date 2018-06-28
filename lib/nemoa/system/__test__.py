# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa

from nemoa.common.unittest import TestSuite as NmTestSuite

class TestSuite(NmTestSuite):

    def test_system_import(self):
        with self.subTest(filetype = "ini"):
            system = nemoa.system.open('dbn', workspace = 'testsuite')
            test = nemoa.common.type.issystem(system)
            self.assertTrue(test)
