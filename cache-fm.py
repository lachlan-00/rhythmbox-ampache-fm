#!/usr/bin/env python3

"""       Copyright (C)2017
       Lachlan de Waard <lachlan.00@gmail.com>
       --------------------------------------
       Rhythmbox Cache.FM
       --------------------------------------

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.    
    
 This program is distributed in the hope that it will be useful,    
 but WITHOUT ANY WARRANTY; without even the implied warranty of    
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the    
 GNU General Public License for more details.    

 You should have received a copy of the GNU General Public License    
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import codecs
import configparser
import gi
import os
import shutil
import time

gi.require_version('Peas', '1.0')
gi.require_version('PeasGtk', '1.0')
gi.require_version('Notify', '0.7')
gi.require_version('RB', '3.0')

from gi.repository import GObject, Peas, PeasGtk, Gio, Gtk  # , Notify
from gi.repository import RB


PLUGIN_PATH = 'plugins/cache-fm/'
CONFIGFILE = 'cfm.conf'
CONFIGTEMPLATE = 'cfm.conf.template'
UIFILE = 'config.ui'
C = 'conf'


class CacheFm(GObject.Object, Peas.Activatable, PeasGtk.Configurable):
    __gtype_name__ = 'cache-fm'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.Object.__init__(self)
        RB.BrowserSource.__init__(self, name=_('cache-fm'))
        self.plugin_info = 'cache-fm'
        self.conf = configparser.RawConfigParser()
        self.configfile = RB.find_user_data_file(PLUGIN_PATH + CONFIGFILE)
        self.ui_file = RB.find_user_data_file(PLUGIN_PATH + UIFILE)
        self.shell = None
        self.rbdb = None
        self.db = None
        self.player = None
        self.source = None
        self.queue = None
        self.app = None
        self.playing_changed_id = None

        # fields for current track
        self.nowtime = None
        self.nowtitle = None
        self.nowartist = None
        self.nowalbum = None
        self.nowMBtitle = None
        self.nowMBartist = None
        self.nowMBalbum = None

        # Fields for the last saved track to check against
        self.lasttime = int(time.time())
        self.lasttitle = None
        self.lastartist = None
        self.lastalbum = None
        self.lastMBtitle = None
        self.lastMBartist = None
        self.lastMBalbum = None

    def do_activate(self):
        """ Activate the plugin """
        print('activating cache-fm')
        shell = self.object
        self.shell = shell
        self.rbdb = shell.props.db
        self.db = shell.props.db
        self.player = shell.props.shell_player
        self.source = RB.Shell.props.selected_page
        self.queue = RB.Shell.props.queue_source
        self.app = Gio.Application.get_default()
        self.playing_changed_id = self.player.connect('playing-changed',
                                                      self.playing_changed)
        self._check_configfile()

    def do_deactivate(self):
        """ Deactivate the plugin """
        print('deactivating cache-fm')
        Gio.Application.get_default()
        del self.shell
        del self.rbdb
        del self.db
        del self.player
        del self.source
        del self.queue
        del self.app
        del self.playing_changed_id

    def playing_changed(self, shell_player, playing):
        """ When playback entry has changed, get the tags and compare """
        entry = self.player.get_playing_entry()
        if not entry:
            return None, None, None
        self.nowtime = int(time.time())

        # Get name/string tags
        self.nowtitle = entry.get_string(RB.RhythmDBPropType.TITLE)
        self.nowartist = entry.get_string(RB.RhythmDBPropType.ARTIST)
        self.nowalbum = entry.get_string(RB.RhythmDBPropType.ALBUM)

        # Get musicbrainz details
        self.nowMBtitle = entry.get_string(RB.RhythmDBPropType.MB_TRACKID)
        self.nowMBartist = entry.get_string(RB.RhythmDBPropType.MB_ARTISTID)
        # Try album artist if artist is missing
        if not self.nowMBartist:
            self.nowMBartist = entry.get_string(RB.RhythmDBPropType.MB_ALBUMARTISTID)
        self.nowMBalbum = entry.get_string(RB.RhythmDBPropType.MB_ALBUMID)

        self.compare_track()

    def compare_track(self):
        """ Write changes when time and data is different """
        if not (self.nowtitle == self.lasttitle and
                self.nowtitle == self.lastartist and
                self.nowalbum == self.lastalbum):
            # The song has changed so update
            self.lasttitle = self.nowtitle
            self.lastartist = self.nowartist
            self.lastalbum = self.nowalbum
            self.lastMBtitle = self.nowMBtitle
            self.lastMBartist = self.nowMBartist
            self.lastMBalbum = self.nowMBalbum
            # Wait a small amount of time to allow for skipping
            if int(self.nowtime - self.lasttime) > 5:
                # Log track details in last.fm format
                # date	title	artist	album	m title	m artist	m album
                self.log_processing((str(self.nowtime) + '\t' + self.nowtitle +
                                     '\t' + self.nowartist + '\t' +
                                     self.nowalbum + '\t' + self.nowMBtitle +
                                     '\t' + self.nowMBartist +
                                     '\t' + self.nowMBalbum))
            else:
                print(str(int(self.nowtime - self.lasttime)) + 'seconds is too quick to log')
            # Even if no song is logged, timer should be reset.
            self.lasttime = self.nowtime
        return

    def _check_configfile(self):
        """ Copy the default config template or load existing config file """
        if not os.path.isfile(self.configfile):
            template = RB.find_user_data_file(PLUGIN_PATH + CONFIGTEMPLATE)
            folder = os.path.split(self.configfile)[0]
            if not os.path.exists(folder):
                os.makedirs(folder)
            shutil.copyfile(template, self.configfile)
            # set default path for the user
            self.conf.read(self.configfile)
            self.conf.set(C, 'log_path', os.path.join(RB.user_cache_dir(), 'cache-fm.txt'))
            datafile = open(self.configfile, 'w')
            self.conf.write(datafile)
            datafile.close()
        else:
            self.conf.read(self.configfile)
        return

    # Create the Configure window in the rhythmbox plugins menu
    def do_create_configure_widget(self):
        """ Load the glade UI for the config window """
        build = Gtk.Builder()
        build.add_from_file(self.ui_file)
        self._check_configfile()
        self.conf.read(self.configfile)
        window = build.get_object('cache-fm')
        build.get_object('closebutton').connect('clicked',
                                                lambda x:
                                                window.destroy())
        build.get_object('savebutton').connect('clicked', lambda x:
                                               self.save_config(build))
        build.get_object('log_path').set_text(self.conf.get(C, 'log_path'))
        build.get_object('log_limit').set_text(self.conf.get(C, 'log_limit'))
        if self.conf.get(C, 'log_rotate') == 'True':
            build.get_object('log_rotate').set_active(True)
        window.show_all()
        return window

    def save_config(self, builder):
        """ Save changes to the plugin config """
        if builder.get_object('log_rotate').get_active():
            self.conf.set(C, 'log_rotate', 'True')
        else:
            self.conf.set(C, 'log_rotate', 'False')
        self.conf.set(C, 'log_path',
                      builder.get_object('log_path').get_text())
        self.conf.set(C, 'log_limit',
                      builder.get_object('log_limit').get_text())
        datafile = open(self.configfile, 'w')
        self.conf.write(datafile)
        datafile.close()

    def log_processing(self, logmessage):
        """ Perform log operations """
        self.conf.read(self.configfile)
        log_path = self.conf.get(C, 'log_path')
        log_rotate = self.conf.get(C, 'log_rotate')
        log_limit = self.conf.get(C, 'log_limit')
        # Check if just a folder is used
        if os.path.isdir(log_path):
            print('Your log_path is a directory. Adding default filename')
            log_path = os.path.join(log_path, 'cache-fm.txt')
        # Fallback cache file to home folder
        elif not log_path:
            log_path = os.path.join(os.getenv('HOME'), '/cache-fm.txt')
        print('Writing to ' + log_path)
        # Create if missing or over the size limit
        if not os.path.exists(log_path):
            files = codecs.open(log_path, 'w', 'utf8')
            files.close()
        elif os.path.getsize(log_path) >= int(log_limit) and log_rotate == 'True':
            print('rotating large cache file')
            shutil.copyfile(log_path, log_path.replace('.txt', (str(int(time.time())) + '.txt')))
            files = codecs.open(log_path, 'w', 'utf8')
            files.close()
        files = codecs.open(log_path, 'a', 'utf8')
        try:
            logline = [logmessage]
            files.write((u''.join(logline)) + u'\n')
        except UnicodeDecodeError:
            print('LOG UNICODE ERROR')
            logline = [logmessage.decode('utf-8')]
            files.write((u''.join(logline)) + u'\n')
        files.close()
        return


class PythonSource(RB.Source):
    """ Register with rhythmbox """
    def __init__(self):
        RB.Source.__init__(self)
        GObject.type_register_dynamic(PythonSource)
