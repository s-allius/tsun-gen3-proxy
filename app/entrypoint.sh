#!/bin/sh
set -e

user="$(id -u)"
echo "#############################################"
echo "# start: '$SERVICE_NAME'"
echo "# with UserID:$UID, GroupID:$GID"
echo "#############################################"

if [ "$user" = '0' ]; then
	[ -d "/home/$SERVICE_NAME" ] && chown -R $SERVICE_NAME:$SERVICE_NAME /home/$SERVICE_NAME || true
    exec gosu $SERVICE_NAME "$@"
else
    exec "$@"
fi
