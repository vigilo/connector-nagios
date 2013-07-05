NAME := connector-nagios
USER := vigilo-nagios

all: build settings.ini

include buildenv/Makefile.common.python

settings.ini: settings.ini.in
	sed -e 's,@LOCALSTATEDIR@,$(LOCALSTATEDIR),g' \
		-e 's,@SYSCONFDIR@,$(SYSCONFDIR),g' \
		-e 's,@NAGIOSCMDPIPE@,$(NAGIOSCMDPIPE),g' $^ > $@

install: build install_python install_data install_permissions
	# regénérer le dropin.cache de twisted
	-$(PYTHON) -c "from twisted.scripts.twistd import run; run()" > /dev/null 2>&1
install_pkg: build install_python_pkg install_data

install_python: settings.ini $(PYTHON)
	$(PYTHON) setup.py install --record=INSTALLED_FILES
install_python_pkg: settings.ini $(PYTHON)
	$(PYTHON) setup.py install --single-version-externally-managed \
		$(SETUP_PY_OPTS) --root=$(DESTDIR)

install_data: pkg/init pkg/initconf
	# init
	install -p -m 755 -D pkg/init $(DESTDIR)/etc/rc.d/init.d/$(PKGNAME)
	echo /etc/rc.d/init.d/$(PKGNAME) >> INSTALLED_FILES
	install -p -m 644 -D pkg/initconf $(DESTDIR)$(INITCONFDIR)/$(PKGNAME)
	echo $(INITCONFDIR)/$(PKGNAME) >> INSTALLED_FILES

install_permissions:
	@echo "Creating the $(USER) user..."
	-/usr/sbin/groupadd $(USER)
	-/usr/sbin/useradd -s /sbin/nologin -M -g $(USER) -G nagios \
		-d $(LOCALSTATEDIR)/lib/vigilo/$(NAME) \
		-c 'Vigilo $(NAME) user' $(USER)
	@echo "Adding nagios to $(USER) group..."
	-/usr/sbin/usermod -a -G $(USER) nagios
	chown $(USER):$(USER) \
			$(DESTDIR)$(LOCALSTATEDIR)/lib/vigilo/$(NAME) \
			$(DESTDIR)$(LOCALSTATEDIR)/log/vigilo/$(NAME) \
			$(DESTDIR)$(LOCALSTATEDIR)/run/$(PKGNAME)
	chmod 750 $(DESTDIR)$(LOCALSTATEDIR)/lib/vigilo/$(NAME)
	chown root:$(USER) $(DESTDIR)$(SYSCONFDIR)/vigilo/$(NAME)/settings.ini
	chmod 640 $(DESTDIR)$(SYSCONFDIR)/vigilo/$(NAME)/settings.ini

clean: clean_python
	rm -f settings.ini

lint: lint_pylint
tests: tests_nose
doc: apidoc sphinxdoc

.PHONY: install_pkg install_python install_python_pkg install_data install_permissions

# vim: set noexpandtab :
