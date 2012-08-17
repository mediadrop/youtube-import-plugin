# -*- coding: UTF-8 -*-
# This file is a part of the YouTube Import plugin for MediaCore CE.
# The source code contained in this file is licensed under the GPL v3 (or at 
# your option any later version).
# See LICENSE.txt in the main project directory for more information.

import sys

__all__ = ['CLIProgressReporter']

class DummyProgressBar(object):
    def __init__(self, maxval=None, label=None):
        self._label = label
    
    def start(self):
        if self._label:
            sys.stdout.write(self._label)
            sys.stdout.flush()
        return self
    
    def update(self, value):
        sys.stdout.write('.')
        sys.stdout.flush()
    
    def finish(self):
        sys.stdout.write('\n')
        sys.stdout.flush()


class CLIProgressReporter(object):
    def __init__(self, importer, label=''):
        self.importer = importer
        self._label = label
        
        self.count = 0
        self.progressbar = None
    
    def _create_progressbar(self, max_count):
        try:
            from progressbar import ProgressBar, Percentage, Bar
            widgets = [self._label, Percentage(), Bar()]
            return ProgressBar(widgets=widgets, maxval=max_count)
        except ImportError:
            return DummyProgressBar(label=self._label)
    
    def register(self):
        self.importer.add_video_observer(self.new_video)
        self.importer.add_feed_page_observer(self.new_feed_page)
    
    def unregister(self):
        if self.progressbar:
            self.progressbar.finish()
        self.importer.remove_observer(self.new_video)
        self.importer.remove_observer(self.new_feed_page)
    
    def new_video(self, youtube_id):
        self.count += 1
        self.progressbar.update(self.count)
    
    def new_feed_page(self, feed):
        if self.progressbar is None:
            total = int(feed.total_results.text)
            self.progressbar = self._create_progressbar(total).start()

