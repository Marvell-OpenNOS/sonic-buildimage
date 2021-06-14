#!/bin/bash

DEPENDENT="radv dhcp_relay"
MULTI_INST_DEPENDENT="teamd"

function debug()
{
    /usr/bin/logger $1
    /bin/echo `date` "- $1" >> ${DEBUGLOG}
}

function lock_service_state_change()
{
    debug "Locking ${LOCKFILE} from ${SERVICE}$DEV service"

    exec {LOCKFD}>${LOCKFILE}
    /usr/bin/flock -x ${LOCKFD}
    trap "/usr/bin/flock -u ${LOCKFD}" 0 2 3 15

    debug "Locked ${LOCKFILE} (${LOCKFD}) from ${SERVICE}$DEV service"
}

function unlock_service_state_change()
{
    debug "Unlocking ${LOCKFILE} (${LOCKFD}) from ${SERVICE}$DEV service"
    /usr/bin/flock -u ${LOCKFD}
}

function check_warm_boot()
{
    SYSTEM_WARM_START=`$SONIC_DB_CLI STATE_DB hget "WARM_RESTART_ENABLE_TABLE|system" enable`
    SERVICE_WARM_START=`$SONIC_DB_CLI STATE_DB hget "WARM_RESTART_ENABLE_TABLE|${SERVICE}" enable`
    if [[ x"$SYSTEM_WARM_START" == x"true" ]] || [[ x"$SERVICE_WARM_START" == x"true" ]]; then
        WARM_BOOT="true"
    else
        WARM_BOOT="false"
    fi
}

function check_fast_boot()
{
    if [[ $($SONIC_DB_CLI STATE_DB GET "FAST_REBOOT|system") == "1" ]]; then
        FAST_BOOT="true"
    else
        FAST_BOOT="false"
    fi
}

function validate_restore_count()
{
    if [[ x"$WARM_BOOT" == x"true" ]]; then
        RESTORE_COUNT=`$SONIC_DB_CLI STATE_DB hget "WARM_RESTART_TABLE|orchagent" restore_count`
        # We have to make sure db data has not been flushed.
        if [[ -z "$RESTORE_COUNT" ]]; then
            WARM_BOOT="false"
        fi
    fi
}

function wait_for_database_service()
{
    # Wait for redis server start before database clean
    until [[ $($SONIC_DB_CLI PING | grep -c PONG) -gt 0 ]]; do
      sleep 1;
    done

    # Wait for configDB initialization
    until [[ $($SONIC_DB_CLI CONFIG_DB GET "CONFIG_DB_INITIALIZED") ]];
        do sleep 1;
    done
}

# This function cleans up the tables with specific prefixes from the database
# $1 the index of the database
# $2 the string of a list of table prefixes
function clean_up_tables()
{
    $SONIC_DB_CLI $1 EVAL "
    local tables = {$2}
    for i = 1, table.getn(tables) do
        local matches = redis.call('KEYS', tables[i])
        for j,name in ipairs(matches) do
            redis.call('DEL', name)
        end
    end" 0
}

start_peer_and_dependent_services() {
    check_warm_boot

    if [[ x"$WARM_BOOT" != x"true" ]]; then
        if [[ ! -z $DEV ]]; then
            /bin/systemctl start ${PEER}@$DEV
        else
           /bin/systemctl start ${PEER}
        fi
        for dep in ${DEPENDENT}; do
            /bin/systemctl start ${dep}
        done
        for dep in ${MULTI_INST_DEPENDENT}; do
            if [[ ! -z $DEV ]]; then
                /bin/systemctl start ${dep}@$DEV
            else
                /bin/systemctl start ${dep}
            fi
        done
    fi
}

stop_peer_and_dependent_services() {
    # if warm/fast start enabled or peer lock exists, don't stop peer service docker
    if [[ x"$WARM_BOOT" != x"true" ]] && [[ x"$FAST_BOOT" != x"true" ]]; then
        for dep in ${MULTI_INST_DEPENDENT}; do
            if [[ ! -z $DEV ]]; then
                /bin/systemctl stop ${dep}@$DEV
            else
                /bin/systemctl stop ${dep}
            fi
        done
        for dep in ${DEPENDENT}; do
            /bin/systemctl stop ${dep}
        done
        if [[ ! -z $DEV ]]; then
            /bin/systemctl stop ${PEER}@$DEV
        else
            /bin/systemctl stop ${PEER}
        fi
    fi
}

start() {
    debug "Starting ${SERVICE}$DEV service..."

    lock_service_state_change

    wait_for_database_service
    check_warm_boot
    validate_restore_count

    debug "Warm boot flag: ${SERVICE}$DEV ${WARM_BOOT}."

    # Don't flush DB during warm boot
    if [[ x"$WARM_BOOT" != x"true" ]]; then
        debug "Flushing APP, ASIC, COUNTER, CONFIG, and partial STATE databases ..."
        $SONIC_DB_CLI APPL_DB FLUSHDB
        $SONIC_DB_CLI ASIC_DB FLUSHDB
        $SONIC_DB_CLI COUNTERS_DB FLUSHDB
        $SONIC_DB_CLI FLEX_COUNTER_DB FLUSHDB
        clean_up_tables STATE_DB "'PORT_TABLE*', 'MGMT_PORT_TABLE*', 'VLAN_TABLE*', 'VLAN_MEMBER_TABLE*', 'LAG_TABLE*', 'LAG_MEMBER_TABLE*', 'INTERFACE_TABLE*', 'MIRROR_SESSION*', 'VRF_TABLE*', 'FDB_TABLE*', 'FG_ROUTE_TABLE*', 'BUFFER_POOL*', 'BUFFER_PROFILE*', 'MUX_CABLE_TABLE*'"
    fi

    # start service docker
    /usr/bin/${SERVICE}.sh start $DEV
    debug "Started ${SERVICE}$DEV service..."

    # Unlock has to happen before reaching out to peer service
    unlock_service_state_change
}

wait() {
    start_peer_and_dependent_services

    # Allow some time for peer container to start
    # NOTE: This assumes Docker containers share the same names as their
    # corresponding services
    for SECS in {1..60}; do
        if [[ ! -z $DEV ]]; then
            RUNNING=$(docker inspect -f '{{.State.Running}}' ${PEER}$DEV)
        else
            RUNNING=$(docker inspect -f '{{.State.Running}}' ${PEER})
        fi
        ALL_DEPS_RUNNING=true
        for dep in ${MULTI_INST_DEPENDENT}; do
            if [[ ! -z $DEV ]]; then
                DEP_RUNNING=$(docker inspect -f '{{.State.Running}}' ${dep}$DEV)
            else
                DEP_RUNNING=$(docker inspect -f '{{.State.Running}}' ${dep})
            fi
            if [[ x"$DEP_RUNNING" != x"true" ]]; then
                ALL_DEPS_RUNNING=false
                break
            fi
        done

        if [[ x"$RUNNING" == x"true" && x"$ALL_DEPS_RUNNING" == x"true" ]]; then
            break
        else
            sleep 1
        fi
    done

    # NOTE: This assumes Docker containers share the same names as their
    # corresponding services
    for dep in ${MULTI_INST_DEPENDENT}; do
        if [[ ! -z $DEV ]]; then
            ALL_DEPS="$ALL_DEPS ${dep}$DEV"
        else
            ALL_DEPS="$ALL_DEPS ${dep}"
        fi
    done

    if [[ ! -z $DEV ]]; then
        /usr/bin/docker-wait-any -s ${SERVICE}$DEV -d ${PEER}$DEV ${ALL_DEPS}
    else
        /usr/bin/docker-wait-any -s ${SERVICE} -d ${PEER} ${ALL_DEPS}
    fi
}

stop() {
    debug "Stopping ${SERVICE}$DEV service..."

    [[ -f ${LOCKFILE} ]] || /usr/bin/touch ${LOCKFILE}

    lock_service_state_change
    check_warm_boot
    debug "Warm boot flag: ${SERVICE}$DEV ${WARM_BOOT}."
    check_fast_boot
    debug "Fast boot flag: ${SERVICE}$DEV ${FAST_BOOT}."

    # For WARM/FAST boot do not perform service stop
    if [[ x"$WARM_BOOT" != x"true" ]] && [[ x"$FAST_BOOT" != x"true" ]]; then
        /usr/bin/${SERVICE}.sh stop $DEV
        debug "Stopped ${SERVICE}$DEV service..."
    else
        debug "Killing Docker swss..."
        /usr/bin/docker kill swss &> /dev/null || debug "Docker swss is not running ($?) ..."
    fi

    # Flush FAST_REBOOT table when swss needs to stop. The only
    # time when this would take effect is when fast-reboot
    # encountered error, e.g. syncd crashed. And swss needs to
    # be restarted.
    if [[ x"$FAST_BOOT" != x"true" ]]; then
        debug "Clearing FAST_REBOOT flag..."
        clean_up_tables STATE_DB "'FAST_REBOOT*'"
    fi
    # Unlock has to happen before reaching out to peer service
    unlock_service_state_change

    stop_peer_and_dependent_services
}

DEV=$2

SERVICE="swss"
PEER="syncd"
DEBUGLOG="/tmp/swss-syncd-debug$DEV.log"
LOCKFILE="/tmp/swss-syncd-lock$DEV"
NAMESPACE_PREFIX="asic"
if [ "$DEV" ]; then
    NET_NS="$NAMESPACE_PREFIX$DEV" #name of the network namespace
    SONIC_DB_CLI="sonic-db-cli -n $NET_NS"
else
    NET_NS=""
    SONIC_DB_CLI="sonic-db-cli"
fi

case "$1" in
    start|wait|stop)
        $1
        ;;
    *)
        echo "Usage: $0 {start|wait|stop}"
        exit 1
        ;;
esac
