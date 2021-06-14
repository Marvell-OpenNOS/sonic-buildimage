# docker image for centec syncd with rpc

DOCKER_SYNCD_CENTEC_RPC = docker-syncd-centec-rpc.gz
$(DOCKER_SYNCD_CENTEC_RPC)_PATH = $(PLATFORM_PATH)/docker-syncd-centec-rpc
$(DOCKER_SYNCD_CENTEC_RPC)_DEPENDS += $(SYNCD_RPC) $(LIBTHRIFT) $(PTF)
$(DOCKER_SYNCD_CENTEC_RPC)_FILES += $(SUPERVISOR_PROC_EXIT_LISTENER_SCRIPT)
ifeq ($(INSTALL_DEBUG_TOOLS), y)
$(DOCKER_SYNCD_CENTEC_RPC)_DEPENDS += $(SYNCD_RPC_DBG) \
                                      $(LIBSWSSCOMMON_DBG) \
                                      $(LIBSAIMETADATA_DBG) \
                                      $(LIBSAIREDIS_DBG)
endif
$(DOCKER_SYNCD_CENTEC_RPC)_LOAD_DOCKERS += $(DOCKER_SYNCD_BASE)
SONIC_DOCKER_IMAGES += $(DOCKER_SYNCD_CENTEC_RPC)
ifeq ($(ENABLE_SYNCD_RPC),y)
SONIC_INSTALL_DOCKER_IMAGES += $(DOCKER_SYNCD_CENTEC_RPC)
endif

$(DOCKER_SYNCD_CENTEC_RPC)_CONTAINER_NAME = syncd
$(DOCKER_SYNCD_CENTEC_RPC)_VERSION = 1.0.0-rpc
$(DOCKER_SYNCD_CENTEC_RPC)_PACKAGE_NAME = syncd
$(DOCKER_SYNCD_CENTEC_RPC)_RUN_OPT += --privileged -t
$(DOCKER_SYNCD_CENTEC_RPC)_RUN_OPT += -v /host/machine.conf:/etc/machine.conf
$(DOCKER_SYNCD_CENTEC_RPC)_RUN_OPT += -v /var/run/docker-syncd:/var/run/sswsyncd
$(DOCKER_SYNCD_CENTEC_RPC)_RUN_OPT += -v /etc/sonic:/etc/sonic:ro
