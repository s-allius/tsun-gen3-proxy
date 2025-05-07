ARG SERVICE_NAME="tsun-proxy"
ARG UID=1000
ARG GID=1000

#
# first stage for our base image
FROM python:3.13-alpine AS base

COPY --chmod=0700 ./hardening_base.sh /
RUN apk upgrade --no-cache && \
    apk add --no-cache su-exec=0.2-r3	&& \
    /hardening_base.sh && \
    rm /hardening_base.sh

#
# second stage for building wheels packages
FROM base AS builder

# copy the dependencies file to the root dir and install requirements
COPY ./requirements.txt /root/
RUN apk add --no-cache build-base=0.5-r3 && \
    python -m pip install --no-cache-dir pip==24.3.1 wheel==0.45.1 && \
    python -OO -m pip wheel --no-cache-dir --wheel-dir=/root/wheels -r /root/requirements.txt


#
# third stage for our runtime image
FROM base AS runtime
ARG SERVICE_NAME
ARG VERSION
ARG UID
ARG GID
ARG LOG_LVL=INFO
ARG environment

ENV SERVICE_NAME=$SERVICE_NAME
ENV UID=$UID
ENV GID=$GID 
ENV LOG_LVL=$LOG_LVL
ENV HOME=/home/$SERVICE_NAME

    
# set the working directory in the container
WORKDIR /home/$SERVICE_NAME

VOLUME ["/home/$SERVICE_NAME/log", "/home/$SERVICE_NAME/config"]

# install the requirements from the wheels packages from the builder stage 
# and unistall python packages and alpine package manger to reduce attack surface
COPY --from=builder /root/wheels /root/wheels
COPY --chmod=0700 ./hardening_final.sh .
RUN python -m pip install --no-cache-dir --no-cache --no-index /root/wheels/* && \
    rm -rf /root/wheels && \
    python -m pip uninstall --yes wheel pip && \
    apk --purge del apk-tools && \
    ./hardening_final.sh && \
    rm ./hardening_final.sh


# copy the content of the local src and config directory to the working directory
COPY --chmod=0700 entrypoint.sh /root/entrypoint.sh
COPY src .
COPY translations ./translations
RUN echo ${VERSION} > /proxy-version.txt \
  && date > /build-date.txt
EXPOSE 5005 8127 10000

# command to run on container start
ENTRYPOINT ["/root/entrypoint.sh"]
CMD [ "python3", "./server.py" ]
