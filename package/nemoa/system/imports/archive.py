# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa
import numpy

def filetypes():
    """Get supported archive filetypes for system import."""
    return {
        'npz': 'Numpy Zipped Archive' }

def load(path, **kwargs):
    """Import system from archive file."""
    return Npz(**kwargs).load(path)

class Npz:
    """Import system from numpy zipped archive."""

    settings = None
    default = {}

    def __init__(self, **kwargs):
        self.settings = self.default.copy()
        nemoa.common.dict_merge(kwargs, self.settings)

    def load(self, path):
        copy = numpy.load(path)
        return {
            'config': copy['config'].item(),
            'params': copy['params'].item() }
