# RHYTHMBOX AMPACHE-FM

Scrobble each song played in Rhythmbox to your ampache server.
Alternatively you can also just cache to a local file.
Replace last.fm with your homespun alternative or record playback
which can be synced later to other places/devices.

## Verson 2.0

Everything is working the way it should and we are stable.
I've been trying to break and find issues and work around
anything that's come up.

Please enjoy breaking those last.fm chains!

## INSTALL

To install from the terminal using make:

``` shell
  make install
```

To install from the terminal using python (also checks dependencies!)

``` shell
  python3 ./install.py
```

If you want to install manually, extract to the following directory:

* $HOME/.local/share/rhythmbox/plugins/ampache-fm/

You can test python dependencies by running:
python3 -c "import depends_test; depends_test.check()"

## CONFIGURE

* Cache Location: This can be a Directory or a full file path.
   When using a directory the default filename is added (ampache-fm.txt)
  * /home/user/ampache-fm.txt
  * /home/user/cache

* Cache Size Limit (bytes): The size limit of your log file. (Default 10Mb)

* Rotate Large files: Rename large files with the epoch time they are rotated
  * ampache-fm.txt -> ampache-fm1510722240.txt

## USAGE & FEATURES

I currently use this plugin in conjunction with my ampache scripts
[https://github.com/lachlan-00/ampache-scripts]

Using my generated cache file i import directly into my Ampache database
allowing me to maintain a single point of truth for my playback data.

Using this plugin I have been able to completely remove myself from last.fm
and other external caching services keeping this information under my control.

## COMMAND EXAMPLE

Play music in rhythmbox and then sync with your database.

``` shell
./mysql-connection.py /d:/home/user/ownCloud/ampache-fm.txt
```

## HOMEPAGE

[https://github.com/lachlan-00/ampache-fm]
