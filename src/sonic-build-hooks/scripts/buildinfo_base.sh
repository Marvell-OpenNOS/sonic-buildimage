#!/bin/bash

BUILDINFO_PATH=/usr/local/share/buildinfo

LOG_PATH=$BUILDINFO_PATH/log
VERSION_PATH=$BUILDINFO_PATH/versions
PRE_VERSION_PATH=$BUILDINFO_PATH/pre-versions
DIFF_VERSION_PATH=$BUILDINFO_PATH/diff-versions
BUILD_VERSION_PATH=$BUILDINFO_PATH/build-versions
POST_VERSION_PATH=$BUILDINFO_PATH/post-versions
VERSION_DEB_PREFERENCE=$BUILDINFO_PATH/versions/01-versions-deb
WEB_VERSION_FILE=$VERSION_PATH/versions-web
BUILD_WEB_VERSION_FILE=$BUILD_VERSION_PATH/versions-web

. $BUILDINFO_PATH/config/buildinfo.config

URL_PREFIX=$(echo "${PACKAGE_URL_PREFIX}" | sed -E "s#(//[^/]*/).*#\1#")

log_err()
{
    echo "$1" >> $LOG_PATH/error.log
    echo "$1" 1>&2
}

# Get the real command not hooked by sonic-build-hook package
get_command()
{
    # Change the PATH env to get the real command by excluding the command in the hooked folders
    local path=$(echo $PATH | sed 's#[^:]*buildinfo/scripts:##' | sed "s#/usr/local/sbin:##")
    local command=$(PATH=$path which $1)
    echo $command
}

check_version_control()
{
    # The env variable SONIC_VERSION_CONTROL_COMPONENTS examples:
    # all            -- match all components
    # py2,py3,deb    -- match py2, py3 and deb only
    if [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,all,* ]] || [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,$1,* ]]; then
        echo "y"
    else
        echo "n"
    fi
}

get_url_version()
{
    local package_url=$1
    /usr/bin/curl -Lks $package_url | md5sum | cut -d' ' -f1
}

check_if_url_exist()
{
    local url=$1
    if /usr/bin/curl --output /dev/null --silent --head --fail "$1" > /dev/null 2>&1; then
        echo y
    else
        echo n
    fi
}

download_packages()
{
    local parameters=("$@")
    local filenames=
    declare -A filenames
    for (( i=0; i<${#parameters[@]}; i++ ))
    do
        local para=${parameters[$i]}
        local nexti=$((i+1))
        if [[ "$para" == *://* ]]; then
            local url=$para
            local real_version=

            # Skip to use the proxy, if the url has already used the proxy server
            if [[ $url == ${URL_PREFIX}* ]]; then
                continue
            fi

            if [ "$ENABLE_VERSION_CONTROL_WEB" == y ]; then
                local version=
                local filename=$(echo $url | awk -F"/" '{print $NF}' | cut -d? -f1 | cut -d# -f1)
                [ -f $WEB_VERSION_FILE ] && version=$(grep "^${url}=" $WEB_VERSION_FILE | awk -F"==" '{print $NF}')
                if [ -z "$version" ]; then
                    echo "Failed to verify the package: $url, the version is not specified" 2>&1
                    exit 1
                fi

                local version_filename="${filename}-${version}"
                local proxy_url="${PACKAGE_URL_PREFIX}/${version_filename}"
                local url_exist=$(check_if_url_exist $proxy_url)
                if [ "$url_exist" == y ]; then
                    parameters[$i]=$proxy_url
                    filenames[$version_filename]=$filename
                    real_version=$version
                else
                    real_version=$(get_url_version $url)
                    if [ "$real_version" != "$version" ]; then
                        echo "Failed to verify url: $url, real hash value: $real_version, expected value: $version_filename" 1>&2
                       exit 1
                    fi
                fi
            else
                real_version=$(get_url_version $url)
            fi

            echo "$url==$real_version" >> ${BUILD_WEB_VERSION_FILE}
        fi
    done

    $REAL_COMMAND "${parameters[@]}"
    local result=$?

    for filename in "${!filenames[@]}"
    do
        [ -f "$filename" ] && mv "$filename" "${filenames[$filename]}"
    done

    return $result
}

run_pip_command()
{
    parameters=("$@")

    if [ ! -x "$REAL_COMMAND" ] && [ " $1" == "freeze" ]; then
        return 1
    fi

    if [ "$ENABLE_VERSION_CONTROL_PY" != "y" ]; then
        $REAL_COMMAND "$@"
        return $?
    fi

    local found=n
    local install=n
    local pip_version_file=$PIP_VERSION_FILE
    local tmp_version_file=$(mktemp)
    [ -f "$pip_version_file" ] && cp -f $pip_version_file $tmp_version_file
    for para in "${parameters[@]}"
    do
        ([ "$para" == "-c" ] || [ "$para" == "--constraint" ]) && found=y
        if [ "$para" == "install" ]; then
            install=y
        elif [[ "$para" == *.whl ]]; then
            package_name=$(echo $para | cut -d- -f1 | tr _ .)
            sed "/^${package_name}==/d" -i $tmp_version_file
        fi
    done

    if [ "$found" == "n" ] && [ "$install" == "y" ]; then
        parameters+=("-c")
        parameters+=("${tmp_version_file}")
    fi

    $REAL_COMMAND "${parameters[@]}"
    local result=$?
    rm $tmp_version_file
    return $result
}

ENABLE_VERSION_CONTROL_DEB=$(check_version_control "deb")
ENABLE_VERSION_CONTROL_PY2=$(check_version_control "py2")
ENABLE_VERSION_CONTROL_PY3=$(check_version_control "py3")
ENABLE_VERSION_CONTROL_WEB=$(check_version_control "web")
ENABLE_VERSION_CONTROL_GIT=$(check_version_control "git")
ENABLE_VERSION_CONTROL_DOCKER=$(check_version_control "docker")
