# -*- coding: utf-8 -*-
"""Statistics."""

__author__ = 'Patrick Michl'
__email__ = 'frootlab@gmail.com'
__license__ = 'GPLv3'
__docformat__ = 'google'

from typing import List, Optional
from nemoa.base import catalog

#
# Define Catalog Categories
#

@catalog.category
class Association:
    """Catalog category for :term:`association measures <association measure>`.

    Attributes:
        name: Name of the association measure
        tags: List of strings, that describe the algorithm and allow it to be
            found by browsing or searching.
        classes: Optional list of model class names, that can be processed by
            the algorithm.
        plot: Name of plot class, which is used to interpret the results.
            Supported values are: None, 'Heatmap', 'Histogram', 'Scatter2D' or
            'Graph'. Default: 'Heatmap'.
        directed: Boolean value which indicates if the measure of association is
            dictected. Default: True.
        signed: Boolean value which indicates if the measure of association is
            signed. Default: True.
        normal: Boolean value which indicates if the measure of association is
            normalized. Default: False.

    """
    name: str
    tags: Optional[List[str]] = None
    classes: Optional[List[str]] = None
    plot: str = 'Heatmap'
    directed: bool = True
    signed: bool = True
    normal: bool = False

@catalog.category
class Statistic:
    """Catalog category for sample statistics.

    Sample statistics are measures of some attribute of the individual columns
    of a sample, e.g. the arithmetic mean values. For more information see [1]

    Attributes:
        name: Name of the algorithm
        tags: List of strings, that describe the algorithm and allow it to be
            found by browsing or searching
        classes: Optional list of model class names, that can be processed by
            the algorithm
        plot: Name of plot class, which is used to interpret the results.
            Supported values are: None, 'Heatmap', 'Histogram', 'Scatter2D' or
            'Graph'. The default value is 'Histogram'

    References:
        [1] https://en.wikipedia.org/wiki/Statistic

    """
    name: str
    tags: Optional[List[str]] = None
    classes: Optional[List[str]] = None
    plot: str = 'Histogram'

@catalog.category
class Sampler:
    """Catalog category for statistical samplers.

    Statistical samplers are random functions, that generate samples from a
    desired posterior distribution in Bayesian data analysis. Thereby the
    different approaches exploit properties of the underlying dependency
    structure. For more information see e.g. [1]

    Attributes:
        name: Name of the algorithm
        tags: List of strings, that describe the algorithm and allow it to be
            found by browsing or searching
        classes: Optional list of model class names, that can be processed by
            the algorithm
        plot: Name of plot class, which is used to interpret the results.
            Supported values are: None, 'Heatmap', 'Histogram', 'Scatter2D' or
            'Graph'. The default value is 'Histogram'

    References:
        [1] https://en.wikipedia.org/wiki/Gibbs_sampling

    """
    name: str
    tags: Optional[List[str]] = None
    classes: Optional[List[str]] = None
    plot: str = 'Histogram'