ARG SERVICE_NAME="tsun-proxy"
ARG UID=1000
ARG GID=1000

# set base image (host OS)
FROM python:3.11-alpine AS base
USER root

RUN apk update && \
    apk upgrade
RUN apk add --no-cache su-exec	

FROM base as builder

RUN apk add --no-cache build-base && \
    python -m pip install --no-cache-dir -U pip wheel

# copy the dependencies file to the working directory
COPY ./requirements.txt /root/
RUN python -OO -m pip wheel --no-cache-dir --wheel-dir=/root/wheels -r /root/requirements.txt


#
# second unnamed stage
FROM base
ARG SERVICE_NAME
ARG VERSION
ARG UID
ARG GID
ENV VERSION=$VERSION
ENV SERVICE_NAME=$SERVICE_NAME
ENV UID=$UID
ENV GID=$GID 

    
# set the working directory in the container
WORKDIR /home/$SERVICE_NAME

# update PATH environment variable
ENV HOME=/home/$SERVICE_NAME

VOLUME ["/home/$SERVICE_NAME/log", "/home/$SERVICE_NAME/config"]

# copy only the dependencies installation from the 1st stage image
COPY --from=builder /root/wheels /root/wheels
RUN python -m pip install --no-cache --no-index /root/wheels/*
RUN rm -rf /root/wheels

COPY --chmod=0700 entrypoint.sh /root/entrypoint.sh

# copy the content of the local src and config directory to the working directory
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
