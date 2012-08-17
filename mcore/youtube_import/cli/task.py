# -*- coding: UTF-8 -*-
# This file is a part of the YouTube Import plugin for MediaCore CE.
# The source code contained in this file is licensed under the GPL v3 (or at 
# your option any later version).
# See LICENSE.txt in the main project directory for more information.

import os

from argparse import ArgumentParser
from babel import default_locale
import pylons

from mediacore.lib.i18n import Translator

from mcore.youtube_import.cli.set_up import find_config, init_mediacore
from mcore.youtube_import.util import _


__all__ = ['CommandLineTask']

class CommandLineTask(object):
    
    description = u'generic command line task'
    
    def __init__(self):
        self.options = None
    
    def init(self, locale_map=None):
        locale = default_locale() or 'en'
        translator = Translator(locale, locale_map or {})
        pylons.translator._push_object(translator)
        
        config_file = find_config(default=None)
        parser = self.create_parser(config_file)
        
        options = parser.parse_args()
        if not options.config:
            parser.error(_('Please specify a config file using "--config=<filename>"'))
        init_mediacore(options.config)
        self.validate_options(options, parser)
        self.options = options
        return self
    
    def create_parser(self, extend_parser_callback, config_file=None):
        if not os.path.isfile(config_file or ''):
            config_file = None
        
        parser = ArgumentParser(
            # ArgumentParser tries to use string methods but we might have a lazy
            description=unicode(self.description),
            add_help=True
        )
        config_help = _('MediaCore config file')
        if config_file:
            config_help = _('MediaCore config file (default: "%(file)s")') % {'file': config_file}
        parser.add_argument('--config', dest='config', default=config_file,
            help=config_help)
        self.extend_parser(parser)
        return parser
    
    def extend_parser(self, parser):
        # override to add your options
        pass
    
    def validate_options(self, options, parser):
        pass


