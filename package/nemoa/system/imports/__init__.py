# -*- coding: utf-8 -*-

__author__  = 'Patrick Michl'
__email__   = 'patrick.michl@gmail.com'
__license__ = 'GPLv3'

import nemoa.system.imports.archive
import os

def filetypes(filetype = None):
    """Get supported system import filetypes."""

    type_dict = {}

    # get supported archive filetypes
    archive_types = nemoa.system.imports.archive.filetypes()
    for key, val in archive_types.items():
        type_dict[key] = ('archive', val)

    if filetype == None:
        return {key: val[1] for key, val in type_dict.items()}
    if filetype in type_dict:
        return type_dict[filetype]

    return False

def load(path, filetype = None, **kwargs):
    """Import system from file."""

    # get path
    if os.path.isfile(path):
        pass
    elif 'workspace' in kwargs:
        # import workspace and get path and filetype from workspace
        if not kwargs['workspace'] == nemoa.workspace.name():
            if not nemoa.workspace.load(kwargs['workspace']):
                nemoa.log('error', """could not import system:
                    workspace '%s' does not exist"""
                    % (kwargs['workspace']))
                return  {}
        name = '.'.join([kwargs['workspace'], path])
        config = nemoa.workspace.get('system', name = name)
        if not isinstance(config, dict):
            nemoa.log('error', """could not import system:
                workspace '%s' does not contain system '%s'."""
                % (kwargs['workspace'], path))
            return  {}
        path = config['source']['file']
    else:
        nemoa.log('error', """could not import system:
            file '%s' does not exist.""" % (path))
        return {}

    # if filetype is not given get filtype from file extension
    if not filetype:
        filetype = nemoa.common.get_file_extension(path).lower()

    # test if filetype is supported
    if not filetype in filetypes().keys():
        return nemoa.log('error', """could not import system:
            filetype '%s' is not supported.""" % (filetype))

    module_name = filetypes(filetype)[0]
    if module_name == 'archive':
        system_dict = nemoa.system.imports.archive.load(
            path, **kwargs)
    else:
        return False

    # test system dictionary
    if not system_dict:
        nemoa.log('error', """could not import system:
            file '%s' is not valid.""" % (path))
        return {}

    # update source
    if not 'source' in system_dict['config']:
        system_dict['config']['source'] = {}
    system_dict['config']['source']['file'] = path
    system_dict['config']['source']['filetype'] = filetype

    return system_dict