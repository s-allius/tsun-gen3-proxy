#!/bin/sh
set -e

user="$(id -u)"
export VERSION=$(cat /proxy-version.txt)

echo "######################################################"
echo "# prepare: '$SERVICE_NAME' Version:$VERSION"
echo "# for running with UserID:$UID, GroupID:$GID"
echo "# Image built: $(cat /build-date.txt) "
echo "#"

if [ "$user" = '0' ]; then
    mkdir -p /home/$SERVICE_NAME/log /home/$SERVICE_NAME/config
    
    if ! id $SERVICE_NAME &> /dev/null; then
        echo "# create user"
        addgroup --gid $GID $SERVICE_NAME 2> /dev/null
        adduser -G $SERVICE_NAME -s /bin/false -D -H -g "" -u $UID $SERVICE_NAME
    	chown -R $SERVICE_NAME:$SERVICE_NAME /home/$SERVICE_NAME || true
        rm -fr /usr/sbin/addgroup /usr/sbin/adduser /bin/chown
    fi    
    echo "######################################################"
    echo "#"

    exec su-exec $SERVICE_NAME "$@" -tr './translations/'
else
    exec "$@"
fi
