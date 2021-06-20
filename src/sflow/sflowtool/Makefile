.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(SFLOWTOOL)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :

	rm -fr ./sflowtool
	git clone https://github.com/sflow/sflowtool
	cp -r debian sflowtool

	pushd ./sflowtool
	git checkout -b sflowtool -f 6c2963b
ifeq ($(CROSS_BUILD_ENVIRON), y)
	CC=$(CROSS_CC) CONFIG_SITE=/etc/dpkg-cross/cross-config.$(CONFIGURED_ARCH) LD_LIBRARY_PATH=$(CROSS_LIB_PATH) dpkg-buildpackage -rfakeroot -b -us -uc -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	dpkg-buildpackage -rfakeroot -b -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	popd

	mv $* $(DEST)/

