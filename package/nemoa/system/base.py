# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa
import numpy
import time
import copy

class system:

    def __init__(self, *args, **kwargs):
        """Configure system and system parameters."""

        # set configuration and update units and links
        self._setConfig(kwargs['config'] if 'config' in kwargs else {})

    def configure(self, dataset = None, network = None, *args, **kwargs):
        """Configure system and subsystems to network and dataset."""
        if not hasattr(self.__class__, '_configure') \
            or not callable(getattr(self.__class__, '_configure')):
            return True
        nemoa.log("configure system '%s'" % (self.name()))
        nemoa.setLog(indent = '+1')
        if not self._checkNetwork(network):
            nemoa.log('error', """system could not be configured:
                network is not valid!""")
            nemoa.setLog(indent = '-1')
            return False
        if not self._checkDataset(dataset):
            nemoa.log('error', """system could not be configured:
                dataset is not valid!""")
            nemoa.setLog(indent = '-1')
            return False
        retVal = self._configure(dataset = dataset, network = network,
            *args, **kwargs)
        nemoa.setLog(indent = '-1')
        return retVal

    def setName(self, name):
        """Set name of system."""
        if not isinstance(name, str): return False
        self._config['name'] = name
        return True

    def getConfig(self):
        """Return system configuration as dictionary."""
        return self._config.copy()

    def _setConfig(self, config):
        """Set configuration."""
        # create local configuration dictionary
        if not hasattr(self, '_config'):
            self._config = {'check': {}}
            for key in ['params', 'init', 'optimize']:
                if not key in self._config:
                    self._config[key] = self._default(key)

        # overwrite / merge local with given configuration
        nemoa.common.dictMerge(config, self._config)

        # create / update local unit and link dictionaries
        if not hasattr(self, '_params'): self._params = {}
        self.setUnits(self._getUnitsFromConfig())
        self.setLinks(self._getLinksFromConfig())

        self._config['check']['config'] = True
        return True

    def isConfigured(self):
        """Return configuration state of system."""
        return self._config['check']['config'] \
            and self._config['check']['network'] \
            and self._config['check']['dataset']

    def setNetwork(self, *args, **kwargs):
        """Update units and links to network instance."""
        return self._setNetwork(*args, **kwargs)

    def updateNetwork(self, network):
        """update params in network."""
        if not nemoa.type.isNetwork(network): return False
        G = network.graph
        for u, v, d in G.edges(data = True):
            params = self.getLink((u, v))
            if not params: params = self.getLink((v, u))
            if not params: continue
            nemoa.common.dictMerge(params, G[u][v]['params'])
            G[u][v]['weight'] = params['weight']
        return True

    def setDataset(self, *args, **kwargs):
        """Update units and links to dataset instance."""
        return self._setDataset(*args, **kwargs)

    def _checkNetwork(self, network, *args, **kwargs):
        """Check if network is valid for system."""
        if not nemoa.type.isNetwork(network): return False
        return True

    #2do: there is more to check
    def _checkDataset(self, dataset, *args, **kwargs):
        """Check if network is valid for system."""
        if not nemoa.type.isDataset(dataset): return False
        return True

    def _isEmpty(self):
        """Return true if system is a dummy."""
        return False

    def getUnits(self, **kwargs):
        """.

        Returns:
            Tuple with lists of units that match a given property

        Examples:
            return visible units: getUnits(visible = True)
        """

        filter = []
        for key in kwargs.keys():
            if key == 'group':
                key = 'name'
                kwargs['name'] = kwargs['group']
            if key in self._params['units'][0].keys():
                filter.append((key, kwargs[key]))

        groups = ()
        for group in self._params['units']:
            valid = True
            for key, val in filter:
                if not group[key] == val:
                    valid = False
                    break
            if valid: groups += (group['label'], )

        return groups

    def setUnits(self, units = None, initialize = True):
        """Set units and update system parameters."""
        if not 'units' in self._params: self._params['units'] = []
        if not hasattr(self, 'units'): self.units = {}
        if initialize: return self._setUnits(units) and self._initUnits()
        return self._setUnits(units)

    def getUnitInfo(self, *args, **kwargs):
        """Return dictionary with information about a specific unit."""
        return self._getUnitInformation(*args, **kwargs)

    def unlinkUnit(self, unit):
        """Unlink unit (if present)."""
        return self._unlinkUnit(unit)

    def removeUnits(self, type, label):
        """Remove unit."""
        return self._removeUnit(type, label)

    def getGroups(self, **kwargs):
        """.

        Returns:
            Tuple with groups of units that match a given property

        Examples:
            return visible groups:
                getGroups(visible = True)
            search for group 'MyGroup':
                getGroups(name = 'MyGroup')
        """

        filter = []
        for key in kwargs.keys():
            if key in self._params['units'][0].keys():
                filter.append((key, kwargs[key]))

        groups = ()
        for group in self._params['units']:
            valid = True
            for key, val in filter:
                if not group[key] == val:
                    valid = False
                    break
            if valid: groups += (group['name'], )

        return groups

    def getGroupOfUnit(self, unit):
        """Return name of unit group of given unit."""
        for id in range(len(self._params['units'])):
            if unit in self._params['units'][id]['label']:
                return self._params['units'][id]['name']
        return None

    def setLinks(self, links = None, initialize = True):
        """Set links using list with 2-tuples containing unit labels."""
        if not 'links' in self._params: self._params['links'] = {}
        if not hasattr(self, 'links'): self.links = {}
        if initialize: return self._setLinks(links) \
            and self._indexLinks() and self._initLinks()
        return self._indexLinks()

    def getLinks(self, *args, **kwargs):
        """Return list with 2-tuples containing unit labels."""
        return self._getLinksFromConfig()

    def removeLinks(self, links = [], *args, **kwargs):
        """Remove links from system using list with 2-tuples containing unit labels."""
        return self._removeLinks(links)

    def getLink(self, link):
        srcUnit = link[0]
        tgtUnit = link[1]
        srcGrp  = self.getGroupOfUnit(srcUnit)
        tgtGrp  = self.getGroupOfUnit(tgtUnit)
        if not srcGrp in self._links \
            or not tgtGrp in self._links[srcGrp]['target']: return None
        linkGrp = self._links[srcGrp]['target'][tgtGrp]
        srcID   = self.units[srcGrp].params['label'].index(srcUnit)
        tgtID   = self.units[tgtGrp].params['label'].index(tgtUnit)
        weight  = linkGrp['W'][srcID, tgtID]
        norm    = float(numpy.sum(linkGrp['A'])) / numpy.sum(
            numpy.abs(linkGrp['W']))
        return {
            'adjacency': linkGrp['A'][srcID, tgtID],
            'weight':    weight,
            'normal':    norm * weight}

    def _get(self, section = None):
        """Return system settings as dictionary."""
        dict = {
            'config': copy.deepcopy(self._config),
            'params': copy.deepcopy(self._params) }
        if not section: return dict
        if section in dict: return dict[section]
        return False

    def _set(self, **kwargs):
        """Set system settings from dictionary."""
        if 'config' in kwargs:
            self._config = copy.deepcopy(kwargs['config'])
        if 'params' in kwargs:
            self._params = copy.deepcopy(kwargs['params'])
        return self._updateUnitsAndLinks()

    def initParams(self, dataset = None):
        """Initialize system parameters.

        Initialize all system parameters to dataset.

        Args:
            dataset: nemoa dataset instance
        """
        if not nemoa.type.isDataset(dataset): return nemoa.log('error',
            """could not initilize system parameters:
            invalid dataset instance given!""")
        return self._initParams(dataset)

    def getParams(self, *args, **kwargs):
        """Return dictinary with all system parameters."""
        return copy.deepcopy(self._params)

    def setParams(self, params, update = True):
        """Set system parameters using from dictionary."""
        if not self._checkParams(params): return nemoa.log('error',
            """could not set system parameters:
            invalid 'params' dictionary given!""")
        if update: self._setParams(params)
        else: self._params = copy.deepcopy(params)
        return True

    def resetParams(self, dataset):
        """Reset system parameters using dataset instance."""
        return self.initParams(dataset)

    def optimizeParams(self, dataset, schedule):
        """Optimize system parameters using data and given schedule."""

        # check if optimization schedule exists for current system
        # and merge default, existing and given schedule
        if not 'params' in schedule:
            config = self._default('optimize')
            nemoa.common.dictMerge(self._config['optimize'], config)
            self._config['optimize'] = config
        elif not self.getType() in schedule['params']: return nemoa.log(
            'error', """could not optimize model:
            optimization schedule '%s' does not include system '%s'
            """ % (schedule['name'], self.getType()))
        else:
            config = self._default('optimize')
            nemoa.common.dictMerge(self._config['optimize'], config)
            nemoa.common.dictMerge(schedule['params'][self.getType()], config)
            self._config['optimize'] = config

        # check dataset
        if (not 'checkDataset' in config
            or config['checkDataset'] == True) \
            and not self._checkDataset(dataset): return False

        # initialize tracker
        tracker = nemoa.system.base.tracker(self)
        if 'inspect' in config and not config['inspect'] == False:
            tracker.setTestData(self._getTestData(dataset))

        # optimize system parameters
        algorithm = config['algorithm'].title()
        nemoa.log('note', "optimize '%s' (%s) using algorithm '%s'" % \
            (self.name(), self.getType(), algorithm))
        nemoa.setLog(indent = '+1')
        retVal = self._optParams(dataset, schedule, tracker)
        nemoa.setLog(indent = '-1')

        return retVal

    def _isNetworkMLPCompatible(self, network = None):
        """Test if a network is compatible to multilayer perceptrons.

        Args:
            network: nemoa network instance

        Returns:
            Boolean value which is True if the following conditions are
            satisfied:
            (1) The network contains at least three layers
            (2) All layers of the network are not empty
            (3) The first and last layer of the network are visible,
                all middle layers of the network are hidden
        """

        if not nemoa.type.isNetwork(network): return nemoa.log('error',
            'could not test network: invalid network instance given!')
        if len(network.layers()) < 3: return nemoa.log('error',
            'Multilayer networks need at least three layers!')
        for layer in network.layers():
            if not len(network.layer(layer)['nodes']) > 0: return nemoa.log(
                'error', 'Feedforward networks do not allow empty layers!')
            if not network.layer(layer)['visible'] \
                == (layer in [network.layers()[0], network.layers()[-1]]):
                return nemoa.log('error', """The first and the last layer
                    of a multilayer feedforward network have to be visible,
                    middle layers have to be hidden!""")
        return True

    def _isNetworkDBNCompatible(self, network = None):
        """Test if a network is compatible to deep beliefe networks.

        Args:
            network: nemoa network instance

        Returns:
            Boolean value which is True if the following conditions are
            satisfied:
            (1) The network is MPL compatible:
                see function _isNetworkMPLCompatible
            (2) The network contains an odd number of layers
            (3) The hidden layers are symmetric to the central layer
                related to their number of nodes
        """
        if not nemoa.type.isNetwork(network): return nemoa.log('error',
            'could not test network: invalid network instance given!')
        if not self._isNetworkMLPCompatible(network): return False
        if not len(network.layers()) % 2 == 1: return nemoa.log('error',
            'DBN / Autoencoder networks expect an odd number of layers!')

        layers = network.layers()
        size = len(layers)
        for id in range(1, (size - 1) / 2):
            symmetric = len(network.layer(layers[id])['nodes']) \
                == len(network.layer(layers[-id-1])['nodes'])
            if not symmetric: return nemoa.log('error',
                """DBN / Autoencoder networks expect a symmetric
                number of hidden nodes, related to their central layer!""")
        return True

    def _isDatasetBinary(self, dataset = None):
        """Test if a dataset contains only binary data.

        Args:
            dataset: nemoa dataset instance

        Returns:
            Boolean value which is True if a given dataset contains only
            binary values.
        """

        if not nemoa.type.isDataset(dataset): return nemoa.log('error',
            'could not test dataset: invalid dataset instance given!')

        data = dataset.getData()
        binary = ((data == data.astype(bool)).sum() == data.size)

        if not binary: return nemoa.log('error',
            'The dataset does not contain binary data!')

        return True

    def _isDatasetGaussNormalized(self, dataset = None,
        size = 100000, maxMean = 0.05, maxSdev = 1.05):
        """Test if a dataset contains gauss normalized data.

        Args:
            dataset: nemoa dataset instance
            size: number of samples to create statistics
            maxMean: allowed maximum for absolute mean value
            maxSdev: allowed maximum for standard deviation

        Returns:
            Boolean value which is True if the following conditions are
            satisfied:
            (1) The absolute mean value of a given number of random
                samples of the dataset is below maxMean
            (2) The standard deviation of a given number of random
                samples of the dataset is below maxSdev
        """

        if not nemoa.type.isDataset(dataset): return nemoa.log('error',
            'could not test dataset: invalid dataset instance given!')

        data = dataset.getData(size) # get numpy array with data

        mean = data.mean()
        if numpy.abs(mean) >= maxMean: return nemoa.log('error',
            """Dataset does not contain gauss normalized data:
            mean value is %.3f!""" % (mean))

        sdev = data.std()
        if sdev >= maxSdev: return nemoa.log('error',
            """Dataset does not contain gauss normalized data:
            standard deviation is %.3f!""" % (sdev))

        return True

    def eval(self, data, *args, **kwargs):
        if len(args) == 0:
            return self._evalSystem(data, **kwargs)
        if args[0] == 'units':
            return self._evalUnits(data, *args[1:], **kwargs)
        if args[0] == 'links':
            return self._evalLinks(data, *args[1:], **kwargs)
        if args[0] == 'relations':
            return self._evalRelations(data, *args[1:], **kwargs)
        if args[0] in self._aboutSystem().keys():
            return self._evalSystem(data, *args, **kwargs)
        return nemoa.log('warning',
            "could not evaluate system: unknown method '%s'" % (args[0]))

    @staticmethod
    def _getDataSum(data, norm = 'S'):
        """Return sum of data.

        Args:
            data: numpy array containing data
            norm: data mean norm
                'S': Sum of Values
                'SE', 'L1': Sum of Errors / L1 Norm
                'SSE': Sum of Squared Errors
                'RSSE': Root Sum of Squared Errors
        """

        norm = norm.upper()

        # Sum of Values (S)
        if norm in ['S']: return numpy.sum(data, axis = 0)
        # Sum of Errors (SE) / L1-Norm (L1)
        if norm in ['SE', 'L1']: return numpy.sum(numpy.abs(data), axis = 0)
        # Sum of Squared Errors (SSE)
        if norm in ['SSE']: return numpy.sum(data ** 2, axis = 0)
        # Root Sum of Squared Errors (RSSE)
        if norm in ['RSSE']: return numpy.sqrt(numpy.sum(data ** 2, axis = 0))

        return nemoa.log('error', "unknown data sum norm '%s'" % (norm))

    @staticmethod
    def _getDataMean(data, norm = 'M'):
        """Return mean of data.

        Args:
            data: numpy array containing data
            norm: data mean norm
                'M': Arithmetic Mean of Values
                'ME': Mean of Errors
                'MSE': Mean of Squared Errors
                'RMSE', 'L2': Root Mean of Squared Errors / L2 Norm
        """

        norm = norm.upper()

        # Mean of Values (M)
        if norm in ['M']: return numpy.mean(data, axis = 0)
        # Mean of Errors (ME)
        if norm in ['ME']: return numpy.mean(numpy.abs(data), axis = 0)
        # Mean of Squared Errors (MSE)
        if norm in ['MSE']: return numpy.mean(data ** 2, axis = 0)
        # Root Mean of Squared Errors (RMSE) / L2-Norm (L2)
        if norm in ['RMSE', 'L2']: return numpy.sqrt(numpy.mean(data ** 2, axis = 0))

        return nemoa.log('error', "unknown data mean norm '%s'" % (norm))

    @staticmethod
    def _getDataDeviation(data, norm = 'SD'):
        """Return deviation of data.

        Args:
            data: numpy array containing data
            norm: data deviation norm
                'SD': Standard Deviation of Values
                'SDE': Standard Deviation of Errors
                'SDSE': Standard Deviation of Squared Errors
        """

        norm = norm.upper()

        # Standard Deviation of Data (SD)
        if norm in ['SD']: return numpy.std(data, axis = 0)
        # Standard Deviation of Errors (SDE)
        if norm in ['SDE']: return numpy.std(numpy.abs(data), axis = 0)
        # Standard Deviation of Squared Errors (SDSE)
        if norm in ['SDSE']: return numpy.std(data ** 2, axis = 0)

        return nemoa.log('error', "unknown data deviation norm '%s'" % (deviation))

    def mapData(self, data, mapping = None, transform = 'expect'):
        """Return system representation of data.

        Args:
            mapping: tuple of strings describing the mapping function
            transform: mapping algorithm
        """

        if mapping == None: mapping = self.getMapping()
        if transform == 'expect': return self._evalUnitExpect(data, mapping)
        if transform == 'value':  return self._evalUnitValues(data, mapping)
        if transform == 'sample': return self._evalUnitSamples(data, mapping)
        return nemoa.log('error', """could not map data:
            unknown mapping algorithm '%s'""" % (transform))

    def about(self, *args):
        """Return generic information about various parts of the system.

        Args:
            *args: strings, containing a breadcrump trail to
                a specific information about the system

        Examples:
            about('units', 'error')
                Returns information about the "error" measurement
                function of the systems units.
        """

        # create information dictionary
        about = nemoa.common.dictMerge({
            'name': self.name(),
            'description': self.__doc__,
            'class': self._config['class'],
            'type': self.getType(),
            'units': self._getUnitEvalMethods(),
            'links': self._getLinkEvalMethods(),
            'relations': self._aboutRelations()
        }, self._aboutSystem())

        retDict = about
        path = ['system']
        for arg in args:
            if not isinstance(retDict, dict): return retDict
            if not arg in retDict.keys(): return nemoa.log(
                'warning', "%s has no property '%s'" % (' → '.join(path), arg))
            path.append(arg)
            retDict = retDict[arg]
        if not isinstance(retDict, dict): return retDict
        return {key: retDict[key] for key in retDict.keys()}

    def name(self):
        """Return name of system."""
        return self._config['name'] #if 'name' in self._config else ''

    def getType(self):
        """Return sytem type."""
        return '%s.%s' % (self._config['package'], self._config['class'])

class tracker:

    _inspect = True
    _estimate = True
    _data = None
    _config = None
    _system = None
    _state = {}
    _store = []

    def __init__(self, system = None):
        self._configure(system)

    def _configure(self, system):
        """Configure tracker to given nemoa.system instance."""
        if not nemoa.type.isSystem(system): return nemoa.log('warning',
            'could not configure tracker: system is not valid!')
        if not hasattr(system, '_config'): return nemoa.log('warning',
            'could not configure tracker: system contains no configuration!')
        if not 'optimize' in system._config: return nemoa.log('warning',
            'could not configure tracker: system contains no configuration for optimization!')

        # link system
        self._system = system
        self._inspect = system._config['optimize']['inspect'] \
            if 'inspect' in system._config['optimize'] \
            else True
        self._estimate = system._config['optimize']['inspectEstimateTime'] \
            if 'inspectEstimateTime' in system._config['optimize'] \
            else True

    def setTestData(self, data):
        """Set numpy array with destdata."""
        self._data = data

    def reset(self):
        """Reset inspection."""
        self._state = {}
        self._store = []

    def write(self, id = -1, append = False, **kwargs):
        if len(self._store) == (abs(id) - 1) or append == True:
            self._store.append(kwargs)
            return True
        if len(self._store) < id: return nemoa.log('error',
            'could not write to store, wrong index!')
        self._store[id] = kwargs
        return True

    def epoch(self):
        return self._state['epoch']

    def read(self, id = -1):
        return self._store[id] if len(self._store) >= abs(id) else {}

    def difference(self):
        if not 'inspection' in self._state: return 0.0
        if self._state['inspection'] == None: return 0.0
        if self._state['inspection'].shape[0] < 2: return 0.0
        return self._state['inspection'][-1, 1] - \
            self._state['inspection'][-2, 1]

    def trigger(self):
        """Update epoch and time and calculate """

        cfg = self._system._config['optimize']
        epochTime = time.time()
        if self._state == {}: self._initState()
        self._state['epoch'] += 1
        self._triggerKeyEvent() # check keyboard input

        # estimate time needed to finish current optimization schedule
        if self._estimate and not self._state['estimateEnded']:
            if not self._state['estimateStarted']:
                nemoa.log("""estimating time for calculation
                    of %i updates.""" % (cfg['updates']))
                self._state['estimateStarted'] = True
            if (epochTime - self._state['startTime']) \
                > cfg['inspectEstimateTimeWait']:
                estim = ((epochTime - self._state['startTime']) \
                    / (self._state['epoch'] + 1)
                    * cfg['updates'] * cfg['iterations'])
                estimStr = time.strftime('%H:%M',
                    time.localtime(time.time() + estim))
                nemoa.log('note', 'estimation: %ds (finishing time: %s)'
                    % (estim, estimStr))
                self._state['estimateEnded'] = True

        # evaluate model (in a given time interval)
        if self._inspect: self._triggerEval()
        if self._state['abort']: return 'abort'

        return True

    def _initState(self):

        epochTime = time.time()

        nemoa.log('note', "press 'q' if you want to abort the optimization")
        self._state = {
            'startTime': epochTime,
            'epoch': 0,
            'inspection': None,
            'abort': False}
        if self._inspect: self._state['inspectTime'] = epochTime
        if self._estimate:
            self._state['estimateStarted'] = False
            self._state['estimateEnded'] = False

        return True

    def _triggerKeyEvent(self):
        """Check Keyboard."""

        c = nemoa.common.getch()
        if isinstance(c, str):
            if c == 'q':
                nemoa.log('note', '... aborting optimization')
                self._system._config['optimize']['updates'] = \
                    self._state['epoch']
                self._state['abort'] = True

        return True

    def _triggerEval(self):
        """Evaluate Model."""

        cfg = self._system._config['optimize']
        epochTime = time.time()

        if self._data == None:
            nemoa.log('warning', """
                monitoring the process of optimization is not possible:
                testdata is needed!""")
            self._inspect = False
            return False

        if self._state['epoch'] == cfg['updates']:
            func  = cfg['inspectFunction']
            prop  = self._system.about(func)
            value = self._system.eval(data = self._data, func = func)
            out   = 'final: %s = ' + prop['format']
            return nemoa.log('note', out % (prop['name'], value))

        if ((epochTime - self._state['inspectTime']) \
            > cfg['inspectTimeInterval']) \
            and not (self._estimate \
            and self._state['estimateStarted'] \
            and not self._state['estimateEnded']):
            func  = cfg['inspectFunction']
            prop  = self._system.about(func)
            value = self._system.eval(data = self._data, func = func)
            progr = float(self._state['epoch']) / float(cfg['updates']) * 100.0

            # update time of last evaluation
            self._state['inspectTime'] = epochTime

            # add evaluation to array
            if self._state['inspection'] == None:
                self._state['inspection'] = numpy.array([[progr, value]])
            else: self._state['inspection'] = \
                numpy.vstack((self._state['inspection'], \
                numpy.array([[progr, value]])))

            out = 'finished %.1f%%: %s = ' + prop['format']
            return nemoa.log('note', out % (progr, prop['name'], value))

        return False
