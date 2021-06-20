SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = bash_$(BASH_VERSION_FULL)_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf bash-$(BASH_VERSION_MAJOR)

	dget -u https://launchpad.net/debian/+archive/primary/+sourcefiles/bash/$(BASH_VERSION_FULL)/bash_$(BASH_VERSION_FULL).dsc

	pushd bash-$(BASH_VERSION_MAJOR)
ifeq ($(CROSS_BUILD_ENVIRON), y)
	CONFIG_SITE=/etc/dpkg-cross/cross-config.$(CONFIGURED_ARCH) LD_LIBRARY_PATH=$(CROSS_LIB_PATH) dpkg-buildpackage -us -uc -b -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	mv $* $(DEST)/
