CC=gcc
CFLAGS=-std=gnu99

BINARY = systemd-sonic-generator
MAIN_TARGET = $(BINARY)_1.0.0_$(CONFIGURED_ARCH).deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
ifeq ($(CROSS_BUILD_ENVIRON), y)
	CONFIG_SITE=/etc/dpkg-cross/cross-config.$(CONFIGURED_ARCH) LD_LIBRARY_PATH=$(CROSS_LIB_PATH)  dpkg-buildpackage -us -uc -b -a$(CONFIGURED_ARCH) -Pcross,nocheck  -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	dpkg-buildpackage -us -uc -b -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	mv ../$(MAIN_TARGET) $(DEST)/
	rm ../$(BINARY)-* ../$(BINARY)_*

$(BINARY): systemd-sonic-generator.c
	rm -f ./systemd-sonic-generator

	$(CC) $(CFLAGS) -o $@ $^

install: $(BINARY)
	mkdir -p $(DESTDIR)
	mkdir -p $(DESTDIR)/lib
	mkdir -p $(DESTDIR)/lib/systemd
	mkdir -p $(DESTDIR)/lib/systemd/system-generators
	cp ./systemd-sonic-generator $(DESTDIR)/lib/systemd/system-generators
