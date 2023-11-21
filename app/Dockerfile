ARG SERVICE_NAME="tsun-proxy"
ARG UID=1000
ARG GID=1000

#
# first stage for our base image
FROM python:3.12-alpine AS base
USER root

RUN apk upgrade --no-cache && \
    apk add --no-cache su-exec	

RUN rm -fr /var/spool/cron && \
    rm -fr /etc/crontabs && \
    rm -fr /etc/periodic    
# Remove unnecessary user accounts.
RUN sed -i -r '/^(root)/!d' /etc/group && \
    sed -i -r '/^(root)/!d' /etc/passwd    

# Remove init scripts since we do not use them.
RUN rm -fr /etc/inittab

# Remove kernel tunables since we do not need them.
RUN rm -fr /etc/sysctl* \
    rm -fr /etc/modprobe.d \
    rm -fr /etc/modules \
    rm -fr /etc/mdev.conf

# Remove fstab since we do not need it.
RUN rm -f /etc/fstab

#
# second stage for building wheels packages
FROM base as builder

# copy the dependencies file to the root dir and install requirements
COPY ./requirements.txt /root/
RUN apk add --no-cache build-base && \
    python -m pip install --no-cache-dir -U pip wheel && \
    python -OO -m pip wheel --no-cache-dir --wheel-dir=/root/wheels -r /root/requirements.txt


#
# third stage for our runtime image
FROM base as runtime
ARG SERVICE_NAME
ARG VERSION
ARG UID
ARG GID
ARG LOG_LVL
ARG environment

ENV VERSION=$VERSION
ENV SERVICE_NAME=$SERVICE_NAME
ENV UID=$UID
ENV GID=$GID 
ENV LOG_LVL=$LOG_LVL

    
# set the working directory in the container
WORKDIR /home/$SERVICE_NAME

# update PATH environment variable
ENV HOME=/home/$SERVICE_NAME

VOLUME ["/home/$SERVICE_NAME/log", "/home/$SERVICE_NAME/config"]

# install the requirements from the wheels packages from the builder stage 
# and unistall python packages and alpine package manger to reduce attack surface
COPY --from=builder /root/wheels /root/wheels
RUN python -m pip install --no-cache --no-index /root/wheels/* && \
    rm -rf /root/wheels && \
    python -m pip uninstall --yes setuptools wheel pip && \
    apk --purge del apk-tools


# Remove all but a handful of admin commands and remove dangerous commands.
RUN if [ "$environment" = "production" ] ; then \
  find /sbin /usr/sbin  ! -type d \
  -a ! -name su-exec \
  -a ! -name nologin \
  -a ! -name addgroup \
  -a ! -name adduser \
   -delete; \
  sysdirs="/bin /etc /lib /sbin /usr"; \
  find $sysdirs -xdev \( \
  -name hexdump -o \
  -name chgrp -o \
  -name chmod -o \
  -name ln -o \
  -name od -o \
  -name strings -o \
  -name su \
  \) -delete  \
; fi

# copy the content of the local src and config directory to the working directory
COPY --chmod=0700 entrypoint.sh /root/entrypoint.sh
COPY config .
COPY src .

EXPOSE 5005

# command to run on container start
ENTRYPOINT ["/root/entrypoint.sh"]
CMD [ "python3", "./server.py" ]


LABEL org.opencontainers.image.authors="Stefan Allius"
LABEL org.opencontainers.image.source https://github.com/s-allius/tsun-gen3-proxy
LABEL org.opencontainers.image.description 'The "TSUN Gen3 Micro-Inverter" proxy enables a reliable connection between TSUN third generation inverters and an MQTT broker to integrate the inverter into typical home automations'
LABEL org.opencontainers.image.licenses="BSD-3-Clause"
LABEL org.opencontainers.image.vendor="Stefan Allius"
