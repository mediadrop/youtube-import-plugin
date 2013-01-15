# -*- coding: UTF-8 -*-
# This file is a part of the YouTube Import plugin for MediaCore CE.
# The source code contained in this file is licensed under the GPL v3 (or at 
# your option any later version).
# See LICENSE.txt in the main project directory for more information.

from pylons.i18n.translation import lazify

from mediacore.lib.i18n import _ as mcore_ugettext

__all__ = ['_']

gettext_domain = 'youtube_import'

_ = lazify(lambda msgid: mcore_ugettext(msgid, domain=gettext_domain))
