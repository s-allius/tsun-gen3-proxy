#!/bin/sh
set -e

user="$(id -u)"
echo "######################################################"
echo "# prepare: '$SERVICE_NAME' Version:$VERSION"
echo "# for running with UserID:$UID, GroupID:$GID"
echo "#"

if [ "$user" = '0' ]; then
    mkdir -p /home/$SERVICE_NAME/log /home/$SERVICE_NAME/config
    
    if ! id $SERVICE_NAME &> /dev/null; then
        addgroup --gid $GID $SERVICE_NAME 2> /dev/null
        adduser -G $SERVICE_NAME -s /bin/false -D -H -g "" -u $UID $SERVICE_NAME
    fi    
	chown -R $SERVICE_NAME:$SERVICE_NAME /home/$SERVICE_NAME || true
    echo "######################################################"
    echo "#"

    exec su-exec $SERVICE_NAME "$@"
else
    exec "$@"
fi
