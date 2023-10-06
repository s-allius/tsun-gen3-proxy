#!/bin/sh
set -e

user="$(id -u)"
echo "######################################################"
echo "# prepare: '$SERVICE_NAME' Version:$VERSION"
echo "# for running with UserID:$UID, GroupID:$GID"
echo "#"

if [ "$user" = '0' ]; then
    mkdir -p /home/$SERVICE_NAME/log /home/$SERVICE_NAME/config
    
    if id $SERVICE_NAME ; then
        echo "user still exists"
    else
        addgroup --gid $GID $SERVICE_NAME 2> /dev/null
        adduser --ingroup $SERVICE_NAME --shell /bin/false --disabled-password --no-create-home --comment "" --uid $UID $SERVICE_NAME
    fi    
	chown -R $SERVICE_NAME:$SERVICE_NAME /home/$SERVICE_NAME || true
    echo "######################################################"
    echo "#"

    exec gosu $SERVICE_NAME "$@"
else
    exec "$@"
fi
