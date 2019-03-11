# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Frootlab Developers
# Copyright (C) 2013-2019 Patrick Michl
#
# This file is part of Nemoa, https://github.com/frootlab/nemoa
#
#  Nemoa is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  Nemoa is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License along with
#  Nemoa. If not, see <http://www.gnu.org/licenses/>.
#
"""IPython interactive shell."""

__copyright__ = '2019 Frootlab Developers'
__license__ = 'GPLv3'
__docformat__ = 'google'
__author__ = 'Frootlab Developers'
__email__ = 'frootlab@gmail.com'
__authors__ = ['Patrick Michl <patrick.michl@gmail.com>']

try:
    import IPython
except ImportError as err:
    raise ImportError(
        "requires package ipython: "
        "https://ipython.org/") from err

from nemoa.core import ui

def run(banner: str = '', clear: bool = True) -> None:
    """Start IPython interactive shell in embedded mode."""
    # Bypass IPython excepthook to local 'exepthook', to allow logging of
    # uncaught exceptions
    IShell = IPython.core.interactiveshell.InteractiveShell
    func = IShell.showtraceback
    IShell.showtraceback = ui.bypass_exceptions(func, ui.hook_exception)

    # Clear screen
    if clear:
        ui.clear()

    # Prepare arguments
    config = IPython.terminal.ipapp.load_default_config()
    config.InteractiveShellEmbed = config.TerminalInteractiveShell
    config.update({'InteractiveShellEmbed': {'colors': 'Neutral'}})
    kwds = {'config': config}
    if banner:
        kwds['banner1'] = banner + '\n'

    # Start IPython interactive shell in embedded mode.
    IPython.embed(**kwds)
