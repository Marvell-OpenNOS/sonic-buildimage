#!/bin/sh

#  Copyright (C) 2013 Curt Brune <curt@cumulusnetworks.com>
#
#  SPDX-License-Identifier:     GPL-2.0

##
## Shell archive template
##
## Strings of the form %%VAR%% are replaced during construction.
##

echo -n "Verifying image checksum ..."
sha1=$(sed -e '1,/^exit_marker$/d' "$0" | sha1sum | awk '{ print $1 }')

payload_sha1=%%IMAGE_SHA1%%

if [ "$sha1" != "$payload_sha1" ] ; then
    echo
    echo "ERROR: Unable to verify archive checksum"
    echo "Expected: $payload_sha1"
    echo "Found   : $sha1"
    exit 1
fi

echo " OK."

image_size=$(du "$0" | awk '{print $1}')
# Untar and launch install script in a tmpfs
cur_wd=$(pwd)
export cur_wd
archive_path=$(realpath "$0")
tmp_dir=$(mktemp -d)
if [ "$(id -u)" = "0" ] ; then
    mount -t tmpfs tmpfs-installer $tmp_dir || exit 1
    mount_size=$(df $tmp_dir | tail -1 | tr -s ' ' | cut -d' ' -f4)
    if [ "$mount_size" -lt "$((image_size*3))" ]; then
        #align mount_size to next power of two
        mount_size=$(echo $((image_size*3)) | awk '{ print 2^int(((log($1)/log(2))+ 1)) }')
        mount -o remount,size="${mount_size}K" -t tmpfs tmpfs-installer $tmp_dir || exit 1
    fi
fi
cd $tmp_dir
echo -n "Preparing image archive ..."
sed -e '1,/^exit_marker$/d' $archive_path | tar xf - || exit 1
echo " OK."
cd $cur_wd
if [ -n "$extract" ] ; then
    # stop here
    echo "Image extracted to: $tmp_dir"
    if [ "$(id -u)" = "0" ] && [ ! -d "$extract" ] ; then
        echo "To un-mount the tmpfs when finished type:  umount $tmp_dir"
    fi
    exit 0
fi

$tmp_dir/installer/install.sh
rc="$?"

# clean up
if [ "$(id -u)" = "0" ] ; then
    umount $tmp_dir
fi
rm -rf $tmp_dir

exit $rc
exit_marker
