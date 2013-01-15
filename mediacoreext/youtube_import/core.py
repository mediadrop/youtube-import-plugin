# -*- coding: UTF-8 -*-
# This file is a part of the YouTube Import plugin for MediaCore CE.
# The source code contained in this file is licensed under the GPL v3 (or at 
# your option any later version).
# See LICENSE.txt in the main project directory for more information.

from datetime import datetime
import logging
import re

import gdata.youtube.service
from gdata.service import RequestError

from mediacore.lib.storage import (StorageError, YoutubeStorage, 
    add_new_media_file)
from mediacore.lib.thumbnails import create_default_thumbs_for, has_thumbs
from mediacore.lib.xhtml import clean_xhtml
from mediacore.model import (Author, Media, MediaFile, fetch_row, 
    get_available_slug)
from mediacore.model.meta import DBSession

from mediacoreext.youtube_import.util import _

__all__ = ['parse_channel_names', 'ChannelImportState', 'YouTubeImporter', 
    'YouTubeQuotaExceeded']

log = logging.getLogger(__name__)


def parse_channel_names(channel_string):
    channel_names = []
    for name in channel_string.replace(',', ' ').split():
        # YouTube only allows ASCII letters, digits and dots but other
        # software might insert invisible characters (e.g. u'\u202a',
        # unicode "left-to-right embedding").
        channel_name = re.sub('[^a-zA-Z0-9\.]', '', name)
        if channel_name == '':
            # ignore empty lines
            continue
        channel_names.append(channel_name)
    return channel_names


class YouTubeQuotaExceeded(Exception):
    pass


class YouTubeImporter(object):
    def __init__(self, user, auto_publish=False, tags=(), categories=()):
        self.user = user
        self.auto_publish = auto_publish
        self.tags = tags
        if not isinstance(categories, (list, tuple)):
            categories = [categories]
        self.categories = categories
        
        self._video_guards = []
        self._video_observers = []
        self._feed_observers = []
    
    def import_videos_from_channel(self, channel_name):
        try:
            log.debug('importing videos from YouTube channel %r' % channel_name)
            self._import_channel(channel_name)
        except RequestError, request_error:
            exc_data = request_error.args[0]
            if exc_data['status'] != 403:
                raise
            msg_id = _(u'You have exceeded the traffic quota allowed by YouTube. \n' + \
                u'While some of the videos have been saved, not all of them were \n' + \
                u'imported correctly. Please wait a few minutes and run the \n' + \
                u'import again to continue.')
            raise YouTubeQuotaExceeded(msg_id)
    
    def add_video_guard(self, callback):
        self._video_guards.append(callback)
    
    def add_video_observer(self, callback):
        self._video_observers.append(callback)
    
    def add_feed_page_observer(self, callback):
        self._feed_observers.append(callback)
    
    def remove_observer(self, callback):
        if callback in self._feed_observers:
            self._feed_observers.remove(callback)
        if callback in self._video_observers:
            self._video_observers.remove(callback)
        if callback in self._video_guards:
            self._video_guards.remove(callback)
    
    # --- "protected" ---------------------------------------------------------
    def next_uri(self, feed):
        for link in feed.link:
            if link.rel == 'next':
                return link.href
        return None
    
    def id_for_entry(self, entry):
        player_url = self._player_url_from_entry(entry)
        if player_url is None:
            return None
        return self._id_from_youtube_link(player_url)
    
    # --- internal methods ----------------------------------------------------
    
    def _import_channel(self, channel_name):
        # Since we can only get 50 videos at a time, loop through when a "next"
        # link is present in the returned feed from YouTube
        yt_service = gdata.youtube.service.YouTubeService()
        uri = 'http://gdata.youtube.com/feeds/api/users/%s/uploads?max-results=50' \
            % (channel_name)
        while uri is not None:
            feed = yt_service.GetYouTubeVideoFeed(uri)
            uri = self.next_uri(feed)
            self._feed_page_notification(feed)
            self.import_videos_from_feed(feed)
    
    def import_videos_from_feed(self, feed):
        for entry in feed.entry:
            youtube_id = self.id_for_entry(entry)
            if not self._should_import_video(youtube_id):
                continue
            media = self._import_video(entry)
            self._video_notifcation(youtube_id)
            if media:
                DBSession.add(media)
                DBSession.flush()
    
    def _should_import_video(self, youtube_id):
        for observer in self._video_guards:
            if not observer(youtube_id):
                return False
        return True
    
    def _video_notifcation(self, youtube_id):
        for observer in self._video_observers:
            observer(youtube_id)
    
    def _feed_page_notification(self, feed):
        for observer in self._feed_observers:
            observer(feed)
    
    def _player_url_from_entry(self, entry):
        # Occasionally, there are issues with a video in a feed not being 
        # available (region restrictions, etc). If this happens, just move along.
        if not entry.media.player:
            return None
        return unicode(entry.media.player.url, "utf-8")
    
    def _id_from_youtube_link(self, player_url):
        match = YoutubeStorage.url_pattern.match(player_url)
        if match is None:
            log.debug('Cannot parse YouTube URL: %s' % player_url)
            return None
        video_properties = match.groupdict()
        return video_properties.get('id')
    
    def _media_file_for(self, player_url):
        unique_id = self._id_from_youtube_link(player_url)
        if unique_id is None:
            return None
        return MediaFile.query.filter(MediaFile.unique_id==unique_id).first()
    
    def _has_media_file_for(self, player_url):
        return (self._media_file_for(player_url) is not None)
    
    def _import_video(self, entry):
        player_url = self._player_url_from_entry(entry)
        if not player_url:
            log.debug('Video Feed Error: No player URL? %s' % entry)
            return None
        if self._has_media_file_for(player_url):
            return None
        
        media = fetch_row(Media, u'new')
        media.author = Author(self.user.display_name, self.user.email_address)
        media.reviewed = True
        media.title = unicode(entry.media.title.text, "utf-8")
        if entry.media.description.text:
            encoded_description = unicode(entry.media.description.text, "utf-8")
            media.description = clean_xhtml(encoded_description)
        media.slug = get_available_slug(Media, media.title, media)
        
        if self.tags:
            media.set_tags(unicode(self.tags))
        if self.categories:
            media.set_categories(self.categories)
        try:
            media_file = add_new_media_file(media, url=player_url)
        except StorageError, e:
            log.debug('Video Feed Error: Error storing video: %s at %s' \
                % (e.message, player_url))
            return None
        if not has_thumbs(media):
            create_default_thumbs_for(media)
        media.title = media_file.display_name
        media.update_status()
        if self.auto_publish:
            media.reviewed = 1
            media.encoded = 1
            media.publishable = 1
            media.created_on = datetime.now()
            media.modified_on = datetime.now()
            media.publish_on = datetime.now()
        return media


class ChannelImportState(object):
    def __init__(self, importer):
        self.state = dict(processed=set(), remaining=set(), next=None)
        self.importer = importer
    
    @classmethod
    def from_json(cls, importer, json_data):
        self = ChannelImportState(importer)
        self.state['processed'] = set(json_data['processed'])
        self.state['remaining'] = set(json_data['remaining'])
        self.state['next'] = json_data['next']
        return self
    
    def to_json(self):
        return {
            'processed': list(self.state['processed']),
            'remaining': list(self.state['remaining']),
            'next': self.state['next'],
        }
    
    def register(self):
        self.importer.add_video_guard(self.should_process_video)
        self.importer.add_video_observer(self.new_video)
        self.importer.add_feed_page_observer(self.new_feed_page)
    
    def unregister(self):
        self.importer.remove_observer(self.new_video)
        self.importer.remove_observer(self.new_feed_page)
        self.importer.remove_observer(self.should_process_video)
    
    def is_complete(self):
        return (self.state['next'] is None) \
            and len(self.state['processed']) > 0 \
            and len(self.state['remaining']) == 0
    
    def was_interrupted(self):
        return (self.state['next'] is not None) \
            or len(self.state['remaining']) > 0
    
    def should_process_video(self, youtube_id):
        return (youtube_id not in self.state['processed'])
    
    def new_video(self, youtube_id):
        self.state['remaining'].discard(youtube_id)
        self.state['processed'].add(youtube_id)
    
    def new_feed_page(self, feed):
        ids = [self.importer.id_for_entry(entry) for entry in feed.entry]
        self.state['remaining'] = self.state['remaining'].union(ids)
        self.state['next'] = self.importer.next_uri(feed)
    
    def __repr__(self):
        return 'ChannelImportState<processed=%(processed)r, remaining=%(remaining)r, next=%(next)r' % self.state

