.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -e

MAIN_TARGET = $(FRR)
DERIVED_TARGET = $(FRR_PYTHONTOOLS) $(FRR_DBG) $(FRR_SNMP) $(FRR_SNMP_DBG)
SUFFIX = $(shell date +%Y%m%d\.%H%M%S)
STG_BRANCH = stg_temp.$(SUFFIX)

$(addprefix $(DEST)/, $(MAIN_TARGET)): $(DEST)/% :
	# Build the package
	pushd ./frr
	git checkout -b $(FRR_BRANCH) origin/$(FRR_BRANCH)
	stg branch --create $(STG_BRANCH) $(FRR_TAG)
	stg import -s ../patch/series
	tools/tarsource.sh -V -e '-sonic'

ifeq ($(CROSS_BUILD_ENVIRON), y)
	sed -i "s/dh_auto_configure \-\-/mkdir -p build \&\& dh_auto_configure --builddirectory=build --/g" debian/rules
	sed -i "s/dh_auto_build \-\-/cd build \&\& ln -s ..\/debian debian \&\& dh_auto_build --/g" debian/rules 
	sed -i "s/\tdh_auto_install/\tcd build \&\& dh_auto_install/g" debian/rules
	sed -i "s/tools\/frrinit.sh/build\/tools\/frrinit.sh/g" debian/rules
	sed -i "s/doc\/user\/_build\/texinfo/build\/doc\/user\/_build\/texinfo/g" debian/frr-doc.install
	sed -i "s/doc\/manpages/build\/doc\/manpages/g" debian/frr.manpages
	sed -i "s/doc\/user\/_build\/texinfo/build\/doc\/user\/_build\/texinfo/g" debian/frr-doc.info

	CFLAGS="-I $$CROSS_PERL_CORE_PATH" LDFLAGS=" -L $$CROSS_PKGS_LIB_PATH" CONFIG_SITE=/etc/dpkg-cross/cross-config.$(CONFIGURED_ARCH) LD_LIBRARY_PATH=$(CROSS_LIB_PATH) dpkg-buildpackage -rfakeroot -b -d -us -uc -Ppkg.frr.nortrlib -a$(CONFIGURED_ARCH) -Pcross,nocheck -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
else
	dpkg-buildpackage -rfakeroot -b -us -uc -Ppkg.frr.nortrlib -j$(SONIC_CONFIG_MAKE_JOBS) --admindir $(SONIC_DPKG_ADMINDIR)
endif
	stg undo || true
	git clean -xfdf
	git checkout $(FRR_BRANCH)
	stg branch --delete $(STG_BRANCH)
	git rev-parse --short HEAD | xargs git checkout
ifeq ($(CROSS_BUILD_ENVIRON), y)
	git reset --hard
endif
	git checkout master
	git branch -D $(FRR_BRANCH)
	popd
	mv $(DERIVED_TARGET) $* $(DEST)/

$(addprefix $(DEST)/, $(DERIVED_TARGET)): $(DEST)/% : $(DEST)/$(MAIN_TARGET)
