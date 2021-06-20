SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS += -e

MAIN_TARGET = libsnmp-base_$(SNMPD_VERSION_FULL)_all.deb
DERIVED_TARGETS = snmptrapd_$(SNMPD_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  snmp_$(SNMPD_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  snmpd_$(SNMPD_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  snmp-dbgsym_$(SNMPD_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  snmpd-dbgsym_$(SNMPD_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  libsnmp30_$(SNMPD_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  libsnmp30-dbg_$(SNMPD_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  libsnmp-dev_$(SNMPD_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  libsnmp-perl_$(SNMPD_VERSION_FULL)_$(CONFIGURED_ARCH).deb \
		  tkmib_$(SNMPD_VERSION_FULL)_all.deb

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	rm -rf net-snmp-$(SNMPD_VERSION)

	# download debian net-snmp
	dget -u https://sonicstorage.blob.core.windows.net/debian/pool/main/n/net-snmp/net-snmp_$(SNMPD_VERSION_FULL).dsc

	pushd net-snmp-$(SNMPD_VERSION)
	git init
	git add -f *
	git commit -m "unmodified snmpd source"

	# Apply patches
	stg init
	stg import -s ../patch-$(SNMPD_VERSION)/series

ifeq ($(MULTIARCH_QEMU_ENVIRON), y)
	dpkg-buildpackage -rfakeroot -b -d -us -uc -j1 --admindir $(SONIC_DPKG_ADMINDIR)
else
ifeq ($(CROSS_BUILD_ENVIRON), y)
	sed -i "s/python setup.py/CC=$$CROSS_CC LDSHARED=\"$$CROSS_CC -shared\" python setup.py/g" debian/rules
	sed -i "/opts = NetSNMPGetOpts(\".\/\");/a \$$Params{'CC'} = \"$$CROSS_CC\";\n\$$Params{'LD'} = \"$$CROSS_CC\";" perl/Makefile.PL
	sed -i "/Params{'LDDLFLAGS'} =/i \$$Params{'CC'} = \"$$CROSS_CC\";\n\$$Params{'LD'} = \"$$CROSS_CC\";" perl/default_store/Makefile.PL 
	sed -i "/Params{'LDDLFLAGS'} =/i \$$Params{'CC'} = \"$$CROSS_CC\";\n\$$Params{'LD'} = \"$$CROSS_CC\";" perl/ASN/Makefile.PL	
	sed -i "/Params{'LDDLFLAGS'} =/i \$$Params{'CC'} = \"$$CROSS_CC\";\n\$$Params{'LD'} = \"$$CROSS_CC\";" perl/OID/Makefile.PL
	sed -i "/Params{'LDDLFLAGS'} =/i \$$Params{'CC'} = \"$$CROSS_CC\";\n\$$Params{'LD'} = \"$$CROSS_CC\";" perl/SNMP/Makefile.PL
	sed -i "/Params{'LIBS'}    =/i \$$Params{'CC'} = \"$$CROSS_CC\";\n\$$Params{'LD'} = \"$$CROSS_CC\";" perl/agent/default_store/Makefile.PL
	sed -i "/Params{'LDDLFLAGS'} =/i \$$Params{'CC'} = \"$$CROSS_CC\";\n\$$Params{'LD'} = \"$$CROSS_CC\";" perl/agent/Makefile.PL
	sed -i "/Params{'LDDLFLAGS'} =/i \$$Params{'CC'} = \"$$CROSS_CC\";\n\$$Params{'LD'} = \"$$CROSS_CC\";" perl/TrapReceiver/Makefile.PL
	CFLAGS="-I $$CROSS_PERL_CORE_PATH" LDFLAGS=" -L$$CROSS_PKGS_LIB_PATH" CONFIG_SITE=/etc/dpkg-cross/cross-config.$(CONFIGURED_ARCH) LD_LIBRARY_PATH=$(CROSS_LIB_PATH) dpkg-buildpackage -rfakeroot -b -d -us -uc -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	dpkg-buildpackage -rfakeroot -b -d -us -uc -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
endif
	popd

	mv $(DERIVED_TARGETS) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGETS)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
