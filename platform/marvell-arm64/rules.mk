#include $(PLATFORM_PATH)/sdk.mk
include $(PLATFORM_PATH)/sai.mk
include $(PLATFORM_PATH)/docker-syncd-mrvl.mk
include $(PLATFORM_PATH)/docker-syncd-mrvl-rpc.mk
include $(PLATFORM_PATH)/docker-saiserver-mrvl.mk
include $(PLATFORM_PATH)/libsaithrift-dev.mk
include $(PLATFORM_PATH)/one-image.mk
include $(PLATFORM_PATH)/linux-kernel-arm64.mk
include $(PLATFORM_PATH)/platform-db98cx8540-16cd.mk

INCLUDE_SYSTEM_TELEMETRY = ""


SONIC_ALL += $(SONIC_ONE_IMAGE) \
             $(DOCKER_FPM) 	\
             $(DOCKER_PTF_MRVL) \
             $(DOCKER_SYNCD_MRVL_RPC)

# Inject mrvl sai into syncd
$(SYNCD)_DEPENDS += $(MRVL_SAI)
$(SYNCD)_UNINSTALLS += $(MRVL_DEV)

ifeq ($(ENABLE_SYNCD_RPC),y)
$(SYNCD)_DEPENDS += $(LIBSAITHRIFT_DEV)
endif

# Runtime dependency on mrvl sai is set only for syncd
$(SYNCD)_RDEPENDS += $(MRVL_SAI)
