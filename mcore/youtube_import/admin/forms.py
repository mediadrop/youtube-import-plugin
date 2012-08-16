# -*- coding: UTF-8 -*-
# This file is a part of the YouTube Import plugin for MediaCore CE.
# The source code contained in this file is licensed under the GPL v3 (or at 
# your option any later version).
# See LICENSE.txt in the main project directory for more information.

from tw.forms import CheckBox
from tw.forms.validators import NotEmpty

from mediacore.forms import ListFieldSet, ListForm, TextArea, SubmitButton
from mediacore.forms.admin.categories import CategoryCheckBoxList
from mediacore.model import Category, DBSession

from mcore.youtube_import.util import _

__all__ = ['ImportVideosForm']

class ImportVideosForm(ListForm):
    template = 'admin/box-form.html'
    id = 'settings-form'
    css_class = 'form'
    submit_text = None
    fields = [
        ListFieldSet('youtube', suppress_label=True, legend='',
            css_classes=['details_fieldset'],
            children = [
                TextArea('channel_names', attrs=dict(rows=3, cols=20),
                    label_text=_('Channel Name(s)'),
                    help_text=_('One or more channel names (separated by commas) to import. Please enter only the channel/user name, not the full URL. Please be aware that it may take several minutes for the import to complete. When all videos have been imported, you will be returned to the Media page to manage your new videos.'),
                    validator=NotEmpty),
                CheckBox('auto_publish',
                    label_text=_('Publish Videos'),
                    help_text=_('When this is selected, videos are published automatically when they are imported. Otherwise the videos will be added, but will be waiting for review before being published.')),
                CategoryCheckBoxList('categories',
                    label_text=_('Categories'),
                    options=lambda: DBSession.query(Category.id, Category.name).all()),
                TextArea('tags', label_text=_('Tags'), 
                    attrs=dict(rows=3, cols=15), help_text=_(u'e.g.: puppies, great dane, adorable')),
                SubmitButton('save', default=_('Import'), css_classes=['btn', 'btn-save', 'blue', 'f-rgt']),
            ]
        )
    ]

