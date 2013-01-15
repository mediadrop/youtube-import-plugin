#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# This file is a part of the YouTube Import plugin for MediaCore CE.
# The source code contained in this file is licensed under the GPL v3 (or at 
# your option any later version).
# See LICENSE.txt in the main project directory for more information.

import os

try:
    import json
except ImportError:
    import simplejson as json

from mediacoreext.youtube_import.cli.task import CommandLineTask
from mediacoreext.youtube_import.cli.progress import CLIProgressReporter
from mediacoreext.youtube_import.core import (ChannelImportState, parse_channel_names,
    YouTubeQuotaExceeded, YouTubeImporter)
from mediacoreext.youtube_import.util import _



__all__ = ['CommandLineImport', 'import_command']

class CommandLineImport(CommandLineTask):
    
    description = _('Import YouTube videos into MediaCore')
    
    def __init__(self):
        super(CommandLineImport, self).__init__()
        self.user = None
        self.channel_names = ()
    
    # override from super class
    def init(self):
        i18n_dir = os.path.join(os.path.dirname(__file__), '..', 'i18n')
        super(CommandLineImport, self).init(locale_map={'youtube_import': i18n_dir})
        return self
    
    # override from super class
    def extend_parser(self, parser):
        parser.add_argument('--publish', dest='publish', 
            action='store_true', default=False,
            help=_('immediately publish imported videos'))
        parser.add_argument('--tags', dest='tags', type=unicode,
            help=_('associate new videos with these tags (comma separated list)'))
        parser.add_argument('--categories', dest='categories', type=unicode,
            help=_('associate new videos with these categories (comma separated list)'))
        parser.add_argument('--user', dest='user_name', default=u'admin', type=unicode,
            help=_('MediaCore user name for newly created videos (default: "admin")'))
        
        parser.add_argument('channel', nargs='+',
            help=_('YouTube channel name (e.g. "LinuxMagazine")'))
    
    # override from super class
    def validate_options(self, options, parser):
        self.channel_names = parse_channel_names(','.join(options.channel))
        if len(self.channel_names) == 0:
            parser.error(_('Please specify at least one valid channel'))
        
        from mediacore.model.auth import DBSession, User
        u = DBSession.query(User).filter_by(user_name=unicode(options.user_name))
        if u.count() == 0:
            parser.error(_('Unknown user "%(user_name)s"') % {'user_name': options.user_name})
        self.user = u.one()
    
    
    def is_import_complete(self, states):
        for state in states.values():
            if state.was_interrupted():
                return False
        return True
    
    
    def state_filename(self):
        return os.path.join(os.getcwd(), 'youtube-import.state')
    
    def delete_state(self):
        filename = self.state_filename()
        if os.path.isfile(filename):
            os.unlink(filename)
    
    def load_state(self, importer):
        filename = self.state_filename()
        if not os.path.isfile(filename):
            return {}
        
        file_content = file(filename, 'rb').read().decode('utf-8')
        try:
            json_states = json.loads(file_content)
        except ValueError:
            self.delete_state()
            return {}
        states = {}
        for key, state_data in json_states.items():
            states[key] = ChannelImportState.from_json(importer, state_data)
        return states
    
    def save_state(self, states):
        filename = self.state_filename()
        json_states = {}
        for key, state in states.items():
            json_states[key] = state.to_json()
        file(filename, 'wb').write(json.dumps(json_states))
    
    def import_channels(self):
        from mediacore.model import DBSession
        # MediaCore uses '.flush()' but due to different DBSession setup this
        # will not trigger a commit for command line scripts. Treating 'flush()'
        # as 'commit()' is not 100% right but works well enough here...
        DBSession.flush = DBSession.commit
        
        importer = YouTubeImporter(self.user, self.options.publish, 
                                   self.options.tags, self.options.categories)
        
        print _('Importing...')
        states = self.load_state(importer)
        for name in self.channel_names:
            state = states.get(name, ChannelImportState(importer))
            if state.is_complete():
                continue
            state.register()
            progressbar = CLIProgressReporter(importer, label='  '+name+'  ')
            progressbar.register()
            try:
                try:
                    importer.import_videos_from_channel(name)
                    progressbar.done()
                except YouTubeQuotaExceeded, e:
                    print e.args[0]
                    break
            finally:
                progressbar.unregister()
                state.unregister()
                states[name] = state
        
        if self.is_import_complete(states):
            print _('Import complete')
            self.delete_state()
            return
        self.save_state(states)
        print _('Import paused.')


def import_command():
    youtube = CommandLineImport().init()
    youtube.import_channels()

if __name__ == '__main__':
    import_command()

