# -*- coding: UTF-8 -*-
# This file is a part of the YouTube Import plugin for MediaCore CE.
# The source code contained in this file is licensed under the GPL v3 (or at 
# your option any later version).
# See LICENSE.txt in the main project directory for more information.

from mediacore.lib.helpers import url_for
from mediacore.lib.i18n import _
from mediacore.plugin import events
from mediacore.plugin.events import observes

from mcore.youtube_import.admin.util import gettext_domain

__all__ = []

# --------------------------------------------------------
# Make controller available via url in '/admin/plugins' like the panda stream
# plugin
@observes(events.Environment.routes)
def add_routes(mapper):
    mapper.connect('/admin/plugins/youtube_import',
        controller='youtube_import',
        action='index')
    mapper.connect('/admin/plugins/youtube_import/import',
        controller='youtube_import',
        action='perform_import')


# Add navigation item for admin
@observes(events.plugin_settings_links)
def add_settings_link():
    yield (_('YouTube Import', domain=gettext_domain),
           url_for(controller='/admin/plugins/youtube_import'))
# --------------------------------------------------------

# <a href="${link}" class="${current_url.startswith(link) and 'selected' or None}">YouTube Channel Import</a>

