# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa.system.exports.archive

def filetypes(filetype = None):
    """Get supported system export filetypes."""

    type_dict = {}

    # get supported archive filetypes
    archive_types = nemoa.system.exports.archive.filetypes()
    for key, val in list(archive_types.items()):
        type_dict[key] = ('archive', val)

    if not filetype:
        return {key: val[1] for key, val in list(type_dict.items())}
    if filetype in type_dict:
        return type_dict[filetype]

    return False

def save(system, path = None, filetype = None, workspace = None,
    base = 'user', **kwargs):
    """Export system to file.

    Args:
        system (object): nemoa system instance
        path (str, optional): path of export file
        filetype (str, optional): filetype of export file
        workspace (str, optional): workspace to use for file export

    Returns:
        Boolean value which is True if file export was successful

    """

    from nemoa.common import nclass

    if not classes.nclass(system, 'System'):
        raise ValueError("system is not valid")

    from nemoa.common import ospath

    # get directory, filename and fileextension
    if isinstance(workspace, str) and not workspace == 'None':
        directory = nemoa.path('systems',
            workspace = workspace, base = base)
    elif isinstance(path, str): directory = ospath.dirname(path)
    else: directory = ospath.dirname(system.path)
    if isinstance(path, str): name = ospath.basename(path)
    else: name = system.fullname
    if isinstance(filetype, str): fileext = filetype
    elif isinstance(path, str):
        fileext = ospath.fileext(path) or ospath.fileext(system.path)
    else: fileext = ospath.fileext(system.path)
    path = ospath.join(directory, name + '.' + fileext)

    # get filetype from file extension if not given
    # and test if filetype is supported
    if not filetype: filetype = fileext.lower()
    if filetype not in filetypes(): raise ValueError(
        f"filetype '{filetype}' is not supported.")

    # export to file
    module_name = filetypes(filetype)[0]
    if module_name == 'archive':
        return nemoa.system.exports.archive.save(
            system, path, filetype, **kwargs)

    return False
