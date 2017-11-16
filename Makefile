INSTALLPATH="$(HOME)/.local/share/rhythmbox/plugins/cache-fm/"
INSTALLTEXT="The cache-fm plugin has been installed. You may now restart Rhythmbox and enable the 'cache-fm' plugin."
UNINSTALLTEXT="The cache-fm plugin had been removed. The next time you restart Rhythmbox it will disappear from the plugins list."
PLUGINFILE="cache-fm.plugin"

install-req:
	# Make environment
	mkdir -p $(INSTALLPATH)
	# Copy files, forcefully
	cp $(PLUGINFILE) $(INSTALLPATH) -f
	cp cache-fm.py $(INSTALLPATH) -f
	cp config.ui $(INSTALLPATH) -f
	cp cfm.conf.template $(INSTALLPATH) -f
	cp README.md $(INSTALLPATH) -f
	cp LICENSE $(INSTALLPATH) -f
	cp AUTHORS $(INSTALLPATH) -f

install: install-req
	@echo
	@echo $(INSTALLTEXT)

install-gui: install-req
	# Notify graphically
	zenity --info --title='Installation complete' --text=$(INSTALLTEXT)

uninstall-req:
	# Simply remove the installation path folder
	rm -rf $(INSTALLPATH)

uninstall: uninstall-req
	@echo
	@echo $(UNINSTALLTEXT)

uninstall-gui: uninstall-req
	# Notify graphically
	zenity --info --title='Uninstall complete' --text=$(UNINSTALLTEXT)

