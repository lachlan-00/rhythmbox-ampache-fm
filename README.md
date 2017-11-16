RHYTHMBOX CACHE-FM
==================

Cache each song played in Rhythmbox to a local file.
Useful for recording playback which can be synced later to other places.

Verson 1.0!
-----------

Everything is working the way it should and we are stable.
I've been trying to break and find issues and work around
anything that's come up.

Please enjoy breaking those last.fm chains!

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

CONFIGURE
---------

 * Cache Location: This can be a Directory or a full file path.
   When using a directory the default filename is added (cache-fm.txt)
	* /home/user/cache-fm.txt
    * /home/user/cache

 * Rotate Large files: Rename large files with the epoch time they are rotated
    * cache-fm.txt -> cache-fm1510722240.txt

 * Cache Size Limit (bytes): The size limit of your log file. (Default 10Mb)


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
