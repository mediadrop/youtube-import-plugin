# -*- coding: UTF-8 -*-
# This file is a part of the YouTube Import plugin for MediaCore CE.
# The source code contained in this file is licensed under the GPL v3 (or at 
# your option any later version).
# See LICENSE.txt in the main project directory for more information.

import re
import logging

from gdata.service import RequestError
from pylons import request, tmpl_context as c

from mediacore.lib.base import BaseSettingsController
from mediacore.lib.decorators import autocommit, expose, validate
from mediacore.lib.helpers import redirect, url_for
from mediacore.model import Category

from mcore.youtube_import.admin.forms import *
from mcore.youtube_import.core import YouTubeImporter
from mcore.youtube_import.util import _


__all__ = ['YouTubeImportController']

log = logging.getLogger(__name__)
import_form = ImportVideosForm()

class YouTubeImportController(BaseSettingsController):
    @expose('youtube_import/admin/import.html')
    def index(self, **kwargs):
        category_tree = Category.query.order_by(Category.name).populated_tree()
        return dict(
            form = import_form,
            form_values=kwargs, 
            form_action=url_for(controller='youtube_import', action='perform_import'),
            category_tree = category_tree,
        )

    @expose()
    @validate(import_form, error_handler=index)
    @autocommit
    def perform_import(self, youtube, **kwargs):
        auto_publish = youtube.get('auto_publish', None)
        tags = kwargs.get('youtube.tags')
        categories = kwargs.get('youtube.categories')
        user = request.environ['repoze.who.identity']['user']
        
        channel_names = youtube.get('channel_names', '').replace(',', ' ').split()
        importer = YouTubeImporter(auto_publish, user, tags, categories)
        try:
            for channel_name in channel_names:
                # YouTube only allows ASCII letters, digits and dots but other
                # software might insert invisible characters (e.g. u'\u202a',
                # unicode "left-to-right embedding").
                channel_name = re.sub('[^a-zA-Z0-9\.]', '', channel_name)
                log.debug('importing videos from YouTube channel %r' % channel_name)
                importer.import_videos_from_channel(channel_name)
        except RequestError, request_error:
            if request_error.message['status'] != 403:
                raise
            error_message = _(u'''You have exceeded the traffic quota allowed 
by YouTube. While some of the videos have been saved, not all of them were 
imported correctly. Please wait a few minutes and run the import again to 
continue.''')
            c.form_errors['_the_form'] = error_message
            return self.index(youtube=youtube, **kwargs)
        
        # Redirect to the Media view page, when the import is complete
        redirect(url_for(controller='admin/media', action='index'))

