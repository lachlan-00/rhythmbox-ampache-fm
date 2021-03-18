#!/usr/bin/env python3

"""    Copyright (C)2019
       Lachlan de Waard <lachlan.00@gmail.com>
       --------------------------------------
       Rhythmbox Ampache-FM
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
import csv
import gi
import os
import shutil
import time

import ampache

gi.require_version('Peas', '1.0')
gi.require_version('PeasGtk', '1.0')
gi.require_version('RB', '3.0')

from gi.repository import GObject, Peas, PeasGtk, Gio, Gtk
from gi.repository import RB

from multiprocessing import Process

PLUGIN_PATH = 'plugins/ampache-fm/'
CONFIGFILE = 'afm.conf'
UIFILE = 'config.ui'
C = 'conf'


class AmpacheFm(GObject.Object, Peas.Activatable, PeasGtk.Configurable):
    __gtype_name__ = 'ampache-fm'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.Object.__init__(self)
        RB.BrowserSource.__init__(self, name=_('ampache-fm'))
        self.ampache = ampache.API()
        self.ampache.set_format('json')
        self.plugin_info = 'ampache-fm'
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
        self.elapsed_changed_id = None
        self.spinner = None

        # fields for current track
        self.nowtime = None
        self.nowtitle = None
        self.nowartist = None
        self.nowalbum = None
        self.nowMBtitle = None
        self.nowMBartist = None
        self.nowMBalbum = None

        # Fields for the last saved track to check against
        self.lasttime = None

        # ampache details
        self.ampache_url = None
        self.ampache_user = None
        self.ampache_apikey = None
        self.ampache_password = None
        self.ampache_session = False

    def do_activate(self):
        """ Activate the plugin """
        print('activating ampache-fm')
        shell = self.object
        self.shell = shell
        self.rbdb = shell.props.db
        self.db = shell.props.db
        self.player = shell.props.shell_player
        self.source = RB.Shell.props.selected_page
        self.queue = RB.Shell.props.queue_source
        self.app = Gio.Application.get_default()
        self.elapsed_changed_id = self.player.connect('elapsed-changed',
                                                      self.elapsed_changed)
        self._check_configfile()
        # set initial session value
        self.ampache_user = self.conf.get(C, 'ampache_user')
        self.ampache_url = self.conf.get(C, 'ampache_url')
        self.ampache_apikey = self.conf.get(C, 'ampache_api')
        self.ampache_password = self.conf.get(C, 'ampache_password')
        # Get a session
        self._check_session()

    def do_deactivate(self):
        """ Deactivate the plugin """
        print('deactivating ampache-fm')
        self.nowtime = int(time.time())
        self.cache_now_playing()
        Gio.Application.get_default()
        del self.shell
        del self.rbdb
        del self.db
        del self.player
        del self.source
        del self.queue
        del self.app
        del self.elapsed_changed_id

    def ampache_auth(self, key):
        """ ping ampache for auth key """
        self.ampache_user = self.conf.get(C, 'ampache_user')
        self.ampache_url = self.conf.get(C, 'ampache_url')
        self.ampache_apikey = self.conf.get(C, 'ampache_api')
        self.ampache_password = self.conf.get(C, 'ampache_password')
        if self.ampache_url[:8] == 'https://' or self.ampache_url[:7] == 'http://':
            if key:
                ping = self.ampache.ping(self.ampache_url, key)
                if ping:
                    # ping successful
                    self.ampache_session = ping
                    return ping
            if self.ampache_password:
                mytime = int(time.time())
                passphrase = self.ampache.encrypt_password(self.ampache_password, mytime)
                auth = self.ampache.handshake(self.ampache_url, passphrase, self.ampache_user, mytime)
            else:
                auth = self.ampache.handshake(self.ampache_url, self.ampache.encrypt_string(self.ampache_apikey, self.ampache_user))
            if auth:
                print('handshake successful')
                self.ampache_session = auth
                return auth
        return False

    def elapsed_changed(self, shell_player, elapsed):
        """ When playback entry has changed, get the tags and compare """
        entry = shell_player.get_playing_entry()

        if not elapsed:
            return None, None, None

        if entry:
            self.nowtime = int(time.time())
            songlength = shell_player.get_playing_song_duration()
            if (songlength > 30 and elapsed == 30) or (songlength <= 30 and (songlength - 4) == elapsed):
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

                self.cache_now_playing()

    def cache_now_playing(self):
        """ Cache the track to file or to Ampache if you are able """
        if self._check_session():
            print('Sending scrobble to Ampache: ' + self.nowtitle)
            Process(target=self.ampache.scrobble,
                    args=(self.ampache_url, self.ampache_session, self.nowtitle, self.nowartist, self.nowalbum,
                          self.nowMBtitle, self.nowMBartist, self.nowMBalbum,
                          self.nowtime, 'AmpacheFM Rhythmbox')).start()
        # Log track details in last.fm format
        # date	title	artist	album	m title	m artist	m album
        self.log_processing((str(self.nowtime) + '\t' + self.nowtitle +
                             '\t' + self.nowartist + '\t' +
                             self.nowalbum + '\t' + self.nowMBtitle +
                             '\t' + self.nowMBartist +
                             '\t' + self.nowMBalbum))

    def _check_session(self):
        return self.ampache_auth(self.ampache_session)

    def _check_configfile(self):
        """ Create the default config template or load existing config file """
        if not os.path.isfile(self.configfile):
            folder = os.path.split(self.configfile)[0]
            if not os.path.exists(folder):
                os.makedirs(folder)
            """ create a default config if not available """
            conffile = open(self.configfile, "w")
            conffile.write('[conf]\n' +
                           'ampache_url = \n' +
                           'ampache_user = \n' +
                           'ampache_api = \n' +
                           'ampache_password = \n' +
                           'log_path = ' + os.path.join(RB.user_cache_dir(), 'ampache-fm.txt') + '\n' +
                           'log_rotate = True \n' +
                           'log_limit = 10760720')
            conffile.close()
        # read the conf file
        self.conf.read(self.configfile)
        # updated to add password support
        if not self.conf.has_option(C, 'ampache_password'):
            # set default path for the user
            datafile = open(self.configfile, 'w')
            self.conf.set(C, 'ampache_password', '')
            self.conf.write(datafile)
            datafile.close()
            self.conf.read(self.configfile)
        return

    # Create the Configure window in the rhythmbox plugins menu
    def do_create_configure_widget(self):
        """ Load the glade UI for the config window """
        build = Gtk.Builder()
        build.add_from_file(self.ui_file)
        self._check_configfile()
        self.conf.read(self.configfile)
        window = build.get_object('ampache-fm')
        build.get_object('closebutton').connect('clicked',
                                                lambda x:
                                                window.destroy())
        build.get_object('savebutton').connect('clicked', lambda x:
                                               self.save_config(build))
        build.get_object('backfillbutton').connect('clicked', lambda x:
                                                   self.backfill())
        self.spinner = build.get_object('backfillspinner')
        build.get_object('ampache_url').set_text(self.conf.get(C, 'ampache_url'))
        build.get_object('ampache_user').set_text(self.conf.get(C, 'ampache_user'))
        build.get_object('ampache_api').set_text(self.conf.get(C, 'ampache_api'))
        build.get_object('ampache_password').set_text(self.conf.get(C, 'ampache_password'))
        build.get_object('log_path').set_text(self.conf.get(C, 'log_path'))
        build.get_object('log_limit').set_text(self.conf.get(C, 'log_limit'))
        if self.conf.get(C, 'log_rotate') == 'True':
            build.get_object('log_rotate').set_active(True)
        window.show_all()
        return window

    def save_config(self, builder):
        """ Save changes to the plugin config """
        self.ampache_url = builder.get_object('ampache_url').get_text()
        self.ampache_user = builder.get_object('ampache_user').get_text()
        self.ampache_apikey = builder.get_object('ampache_api').get_text()
        self.ampache_password = builder.get_object('ampache_password').get_text()
        if builder.get_object('log_rotate').get_active():
            self.conf.set(C, 'log_rotate', 'True')
        else:
            self.conf.set(C, 'log_rotate', 'False')
        self.conf.set(C, 'ampache_url', self.ampache_url)
        self.conf.set(C, 'ampache_user', self.ampache_user)
        self.conf.set(C, 'ampache_api', self.ampache_apikey)
        self.conf.set(C, 'ampache_password', self.ampache_password)
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
            log_path = os.path.join(log_path, 'ampache-fm.txt')
        # Fallback cache file to home folder
        elif not log_path:
            log_path = os.path.join(os.getenv('HOME'), '/ampache-fm.txt')
        print('Writing to ' + log_path)
        # Create if missing or over the size limit
        if not os.path.exists(log_path):
            files = codecs.open(log_path, 'w', 'utf8')
            files.close()
        elif os.path.getsize(log_path) >= int(log_limit) and log_rotate == 'True':
            print('rotating large cache file')
            shutil.copyfile(log_path, log_path.replace(log_path[-4:], (str(int(time.time())) + log_path[-4:])))
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

    def backfill(self):
        dumpfile = self.conf.get(C, 'log_path')
        print(self.spinner.get_visible)
        self.spinner.activate()
        self.spinner.start()
        print("Parsing cache file", dumpfile)
        if os.path.isfile(dumpfile):
            with open(dumpfile, 'r') as csvfile:
                openfile = list(csv.reader(csvfile, delimiter='\t', ))
                for row in openfile:
                    while Gtk.events_pending():
                        Gtk.main_iteration()
                    rowtrack = None
                    rowartist = None
                    rowalbum = None
                    trackmbid = None
                    artistmbid = None
                    albummbid = None
                    try:
                        test = row[0]
                    except IndexError:
                        test = None
                    try:
                        test2 = str(int(row[0]))
                    except ValueError:
                        test2 = None
                        # print(row)
                    except IndexError:
                        test2 = None
                        # print(row)
                    if test and test2:
                        # Normalise row data
                        try:
                            if not row[1] == '':
                                rowtrack = row[1]
                            if not row[2] == '':
                                rowartist = row[2]
                            if not row[3] == '':
                                rowalbum = row[3]
                        except IndexError:
                            # missing rows in the tsv
                            pass
                        try:
                            if not row[4] == '':
                                trackmbid = row[4]
                        except IndexError:
                            # missing all the rows in the tsv
                            pass
                        try:
                            if not row[5] == '':
                                artistmbid = row[5]
                        except IndexError:
                            # missing all the rows in the tsv
                            pass
                        try:
                            if not row[6] == '':
                                albummbid = row[6]
                        except IndexError:
                            # missing all the rows in the tsv
                            pass
                        # search ampache db for song
                        if rowtrack and rowartist and rowalbum:
                            if self._check_session():
                                print('Sending scrobble to Ampache: ' + str(rowtrack))
                                Process(target=self.ampache.scrobble,
                                        args=(self.ampache_url, self.ampache_session, str(rowtrack), str(rowartist),
                                              str(rowalbum),
                                              str(trackmbid).replace("None", ""), str(artistmbid).replace("None", ""),
                                              str(albummbid).replace("None", ""),
                                              int(row[0]), 'AmpacheFM Rhythmbox')).start()
        self.spinner.stop()
        while Gtk.events_pending():
            Gtk.main_iteration()


class PythonSource(RB.Source):
    """ Register with rhythmbox """

    def __init__(self):
        RB.Source.__init__(self)
        GObject.type_register_dynamic(PythonSource)
