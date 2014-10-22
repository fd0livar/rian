# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa
import numpy

def filetypes():
    """Get supported archive filetypes for model import."""
    return {
        'npz': 'Numpy Zipped Archive' }

def load(path, **kwargs):
    """Import model from archive file."""
    return Npz(**kwargs).load(path)

class Npz:
    """Import model from numpy zipped archive."""

    settings = {}

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            if key in self.settings.keys():
                self.settings[key] = val

    def load(self, path):
        copy = numpy.load(path)
        return {
            'config': copy['config'].item(),
            'dataset': copy['dataset'].item(),
            'network': copy['network'].item(),
            'system': copy['system'].item() }