ARG SERVICE_NAME="tsun-proxy"
ARG UID=1000
ARG GID=1000

#
# first stage for our base image
FROM python:3.12-alpine AS base
USER root

COPY --chmod=0700 ./hardening_base.sh .
RUN apk upgrade --no-cache && \
    apk add --no-cache su-exec	&& \
    ./hardening_base.sh && \
    rm ./hardening_base.sh

#
# second stage for building wheels packages
FROM base AS builder

# copy the dependencies file to the root dir and install requirements
COPY ./requirements.txt /root/
RUN apk add --no-cache build-base && \
    python -m pip install --no-cache-dir -U pip wheel && \
    python -OO -m pip wheel --no-cache-dir --wheel-dir=/root/wheels -r /root/requirements.txt


#
# third stage for our runtime image
FROM base AS runtime
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
ENV HOME=/home/$SERVICE_NAME

    
# set the working directory in the container
WORKDIR /home/$SERVICE_NAME

VOLUME ["/home/$SERVICE_NAME/log", "/home/$SERVICE_NAME/config", "/home/$SERVICE_NAME/cert"]

# install the requirements from the wheels packages from the builder stage 
# and unistall python packages and alpine package manger to reduce attack surface
COPY --from=builder /root/wheels /root/wheels
COPY --chmod=0700 ./hardening_final.sh .
RUN python -m pip install --no-cache --no-index /root/wheels/* && \
    rm -rf /root/wheels && \
    python -m pip uninstall --yes setuptools wheel pip && \
    apk --purge del apk-tools && \
    ./hardening_final.sh && \
    rm ./hardening_final.sh


# copy the content of the local src and config directory to the working directory
COPY --chmod=0700 entrypoint.sh /root/entrypoint.sh
COPY config .
COPY src .
RUN date > /build-date.txt
EXPOSE 5005 8127 10000 10443

# command to run on container start
ENTRYPOINT ["/root/entrypoint.sh"]
CMD [ "python3", "./server.py" ]


LABEL org.opencontainers.image.title="TSUN Gen3 Proxy"
LABEL org.opencontainers.image.authors="Stefan Allius"
LABEL org.opencontainers.image.source=https://github.com/s-allius/tsun-gen3-proxy
LABEL org.opencontainers.image.description='This proxy enables a reliable connection between TSUN third generation inverters (eg. TSOL MS600, MS800, MS2000) and an MQTT broker to integrate the inverter into typical home automations.'
LABEL org.opencontainers.image.licenses="BSD-3-Clause"
LABEL org.opencontainers.image.vendor="Stefan Allius"
