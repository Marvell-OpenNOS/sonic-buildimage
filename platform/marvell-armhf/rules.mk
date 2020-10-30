#include $(PLATFORM_PATH)/sdk.mk
include $(PLATFORM_PATH)/sai.mk
include $(PLATFORM_PATH)/docker-syncd-mrvl.mk
include $(PLATFORM_PATH)/docker-syncd-mrvl-rpc.mk
include $(PLATFORM_PATH)/docker-saiserver-mrvl.mk
include $(PLATFORM_PATH)/libsaithrift-dev.mk
include $(PLATFORM_PATH)/docker-ptf-mrvl.mk
include $(PLATFORM_PATH)/one-image.mk
include $(PLATFORM_PATH)/linux-kernel-armhf.mk
include $(PLATFORM_PATH)/platform-et6448m.mk

INCLUDE_SYSTEM_TELEMETRY = ""
ENABLE_SYNCD_RPC = ""
INCLUDE_MGMT_FRAMEWORK = ""

SONIC_ALL += $(SONIC_ONE_IMAGE) \
             $(DOCKER_FPM)
             #$(DOCKER_SYNCD_MRVL_RPC)

# Inject mrvl sai into syncd
$(SYNCD)_DEPENDS += $(MRVL_SAI)
$(SYNCD)_UNINSTALLS += $(MRVL_SAI)

ifeq ($(ENABLE_SYNCD_RPC),y)
$(SYNCD)_DEPENDS += $(LIBSAITHRIFT_DEV)
endif

# Runtime dependency on mrvl sai is set only for syncd
$(SYNCD)_RDEPENDS += $(MRVL_SAI)
