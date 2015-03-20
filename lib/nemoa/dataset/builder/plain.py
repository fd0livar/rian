# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa
import numpy

def types():
    """Get supported plain dataset types for dataset building."""

    return {
        'rules': 'Simulated data with manipulation rules',
        'system': 'Simulated data using system',
        'model': 'Real data using model'
    }

def build(type = None, *args, **kwargs):
    """Build plain dataset from building parameters."""

    if type == 'rules': return Rules(**kwargs).build()

    return False

class Rules:
    """Build dataset based on manipulation rules.

    Example:
        dataset = nemoa.dataset.create('rules',
            name = 'example',
            columns = ['i1', 'i2', 'i3', 'i4', 'o1', 'o2'],
            initialize = 'gauss + bernoulli', sdev = 0.1, abin = 0.5,
            rules = [
                ('o1', 'i1 + i2'),
                ('o2', 'i3 + i4')],
            normalize = 'gauss',
            samples = 10000)

    """

    settings = None
    default = {
        'name': 'data',
        'columns': ['i1', 'i2', 'i3', 'i4', 'o1', 'o2'],
        'rowlabel': 'r%i',
        'samples': 10000,
        'initialize': 'gauss + bernoulli',
        'sdev': .1,
        'abin': .5,
        'rules': [
            ('o1', 'i1 + i2'),
            ('o2', 'i3 + i4')],
        'normalize': ''}

    def __init__(self, **kwargs):
        self.settings = nemoa.common.dict.merge(kwargs, self.default)

    def build(self):

        # create dataset configuration
        name = self.settings['name']
        cols = self.settings['columns']
        rowsize = self.settings['samples']
        config = {
            'name': name,
            'type': 'base.Dataset',
            'columns': tuple(),
            'colmapping': {},
            'colfilter': { '*': ['*:*'] },
            'rowfilter': { '*': ['*:*'], name: [name + ':*'] } }
        for col in cols:
            config['colmapping'][col] = col
            config['columns'] += (('', col), )
        config['table'] = {name: config.copy()}
        config['table'][name]['fraction'] = 1.

        # initialize dataset with random values
        dtype = numpy.dtype({
            'names': ('label',) + tuple(cols),
            'formats': ('<U12',) + ('<f8',) * len(cols) })
        data = numpy.recarray((rowsize, ), dtype)
        rowlabels = [self.settings['rowlabel'] % (i + 1) \
            for i in range(rowsize)]
        data['label'] = rowlabels
        initialize = self.settings['initialize']
        for col in cols:
            if isinstance(initialize, basestring):
                initrule = initialize
            elif isinstance(initialize, dict):
                if not col in initialize:
                    nemoa.log('warning', """could not initialize '%s':
                        init rule not found.""" % col)
                    continue
                if not isinstance(initialize[col], basestring):
                    nemoa.log('warning', """could not initialize '%s':
                        init rule not valid.""" % col)
                    continue
                initrule = initialize[col]
            if 'gauss' in initrule:
                sdev = self.settings['sdev']
                if sdev > 0.:
                    gauss = numpy.random.normal(0., sdev, rowsize)
                else:
                    gauss = numpy.zeros(rowsize)
            if 'bernoulli' in initrule:
                abin = self.settings['abin']
                bernoulli = numpy.random.binomial(1, abin, rowsize)
            try: values = eval(initrule)
            except:
                nemoa.log('warning', """could not initialize '%s':
                    init rule "%s" is not valid.""" % (col, initrule))
                continue
            data[col] = values

        # evaluate manipulation rules
        for col, rule in self.settings['rules']:
            if not col in cols: continue
            for key in cols:
                if not key in rule: continue
                rule = rule.replace(key, "data['%s']" % key)
            random = {}
            for key in ['gauss', 'bernoulli']:
                if not key in rule: continue
                if key == 'gauss':
                    sdev = self.settings['sdev']
                    if sdev > 0.:
                        rvalues = numpy.random.normal(0., sdev, rowsize)
                    else:
                        rvalues = numpy.zeros(rowsize)
                if key == 'bernoulli':
                    abin = self.settings['abin']
                    rvalues = numpy.random.binomial(1, abin, rowsize)
                random[key] = rvalues
                rule.replace(key, "random['%s']" % key)
            try: values = eval(rule)
            except:
                nemoa.log('warning', """could not evaluate manipulation
                    rule "%s".""" % rule)
                continue
            data[col] = values

        # normalize data
        norm = self.settings['normalize']
        if norm == 'gauss':
            for col in cols:
                data[col] = (data[col] - data[col].mean()) \
                    / data[col].std()

        return { 'config': config, 'tables': { name: data } }
