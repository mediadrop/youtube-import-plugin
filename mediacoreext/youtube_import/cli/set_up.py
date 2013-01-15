# -*- coding: UTF-8 -*-
# This file is a part of the YouTube Import plugin for MediaCore CE.
# The source code contained in this file is licensed under the GPL v3 (or at 
# your option any later version).
# See LICENSE.txt in the main project directory for more information.

import os

from paste.deploy import appconfig
from paste.script.util import logging_config
import pylons
from pylons.configuration import config

from mediacore.config.environment import load_environment
from mediacore.lib.i18n import Translator


__all__ = ['find_config', 'init_mediacore']

working_dir = os.getcwd()


class NotSet(object):
    pass

def find_config(config_filename=None, default=NotSet):
    if config_filename:
        return config_filename
    for name in ('deployment.ini', 'development.ini'):
        filename = os.path.join(working_dir, name)
        if os.path.exists(filename):
            return filename
    if default != NotSet:
        return default
    raise ValueError('No config file found.')


def init_mediacore(config_filename):
    def load_config(filename):
        filename = os.path.normpath(os.path.abspath(filename))
        config = appconfig('config:'+filename)
        # Load the logging options
        # (must be done before environment is loaded or sqlalchemy won't log)
        logging_config.fileConfig(filename)
        return config
    
    paste_appconfig = load_config(config_filename)
    
    pylons_config = load_environment(paste_appconfig.global_conf, 
                                          paste_appconfig.local_conf)
    
    config.push_process_config(pylons_config)
    
    def setup_translator(config):
        app_globals = config['pylons.app_globals']
        lang = app_globals.settings['primary_language'] or 'en'
        translator = Translator(lang, _locale_dirs(config))
        pylons.translator._push_object(translator)
    setup_translator(config)


def _locale_dirs(config):
    import mediacore
    from mediacore.plugin import PluginManager
    from formencode.api import get_localedir as get_formencode_localedir
    mediacore_root = os.path.abspath(os.path.dirname(mediacore.__file__))
    locale_map = {
        'mediacore': os.path.join(mediacore_root, 'i18n'),
        'FormEncode': get_formencode_localedir(),
    }
    locale_map.update(PluginManager(config).locale_dirs())
    return locale_map
