# -*- coding: utf-8 -*-
"""Layered networks."""

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa.network.base

class MultiLayer(nemoa.network.base.Network):
    """Network with multi layer layout."""
    pass

class Shallow(nemoa.network.base.Network):
    """Network with shallow layout."""
    pass

class Factor(nemoa.network.base.Network):
    """Network with factor graph layout."""
    pass