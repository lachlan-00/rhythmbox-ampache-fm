RHYTHMBOX CACHE-FM
==================

Cache each song played to a local file.
Useful for recording playback which can be synced later to other places.

INSTALL
-------

To install from the terminal using make:
make install

To check the dependencies, then install using python:
python3 ./install.py

If you want to install manually, extract to the following directory:
 * $HOME/.local/share/rhythmbox/plugins/fileorganizer/

You can test python dependencies by running:
python3 -c "import depends_test; depends_test.check()"

USAGE & FEATURES
----------------

I currently use this plugin in conjunction with my ampache scripts
[https://github.com/lachlan-00/ampache-scripts]

Using my generated cache file i import directly into my Ampache database
allowing me to maintain a single point of truth for my playback data.

Using this plugin I have been able to completely remove myself from last.fm
and other external caching services keeping this information under my control.

COMMAND EXAMPLE
---------------

Play music in rhythmbox and then sync with your database.
~~~
./mysql-connection.py /d:/home/user/ownCloud/cache-fm.txt
~~~

HOMEPAGE
--------

[https://github.com/lachlan-00/cache-fm]
