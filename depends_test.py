#!/usr/bin/env python3

"""
  Ampache-FM: test your dependencies
"""


def check():
    """ Importing all libraries used by ampache-fm """
    clear = False
    try:
        import codecs
        import configparser
        import gi
        import hashlib
        import os
        import shutil
        import time
        import threading
        import urllib.parse
        import urllib.request

        import ampache

        gi.require_version('Peas', '1.0')
        gi.require_version('PeasGtk', '1.0')
        gi.require_version('Notify', '0.7')
        gi.require_version('RB', '3.0')

        from gi.repository import GObject, Peas, PeasGtk, Gio, Gtk
        from gi.repository import RB

        clear = True
    except ImportError as errormsg:
        print('\nDependency Problem\n\n' + str(errormsg))

    if clear:
        print('\nAll ampache-fm dependencies are satisfied\n')
        return True
    else:
        return False
