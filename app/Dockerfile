ARG SERVICE_NAME="tsun-proxy"
ARG UID=1000
ARG GID=1000

# set base image (host OS)
FROM python:3.11-slim-bookworm AS builder

USER root

# install gosu for a better su+exec command
RUN set -eux; \
	apt-get update; \
	apt-get install -y gosu; \
	rm -rf /var/lib/apt/lists/*; \
# verify that the binary works
	gosu nobody true

RUN pip install --upgrade pip


# copy the dependencies file to the working directory
COPY ./requirements.txt .

# install dependencies
RUN pip install --user -r requirements.txt


#
# second unnamed stage
FROM python:3.11-slim-bookworm
ARG SERVICE_NAME
ARG UID
ARG GID
ENV SERVICE_NAME=$SERVICE_NAME
ENV UID=$UID
ENV GID=$GID 



RUN addgroup --gid $GID $SERVICE_NAME && \
    adduser --ingroup $SERVICE_NAME --shell /bin/false --disabled-password --uid $UID $SERVICE_NAME && \
    mkdir -p /home/$SERVICE_NAME/log /home/$SERVICE_NAME/config && \
    chown -R $SERVICE_NAME:$SERVICE_NAME /home/$SERVICE_NAME
#addgroup -S -g 1883 mosquitto 2>/dev/null && \
 #   adduser -S -u 1883 -D -H -h /var/empty -s /sbin/nologin -G mosquitto -g mosquitto mosquitto 2>/dev/null && \
  #  mkdir -p /mosquitto/config /mosquitto/data /mosquitto/log && \
  #  chown -R mosquitto:mosquitto /mosquitto && \
    
# set the working directory in the container
WORKDIR /home/$SERVICE_NAME

# update PATH environment variable
ENV HOME=/home/$SERVICE_NAME
ENV PATH=/home/$SERVICE_NAME/.local:$PATH

VOLUME ["/home/$SERVICE_NAME/log", "/home/$SERVICE_NAME/config"]

# copy only the dependencies installation from the 1st stage image
COPY --from=builder --chown=$SERVICE_NAME:$SERVICE_NAME /root/.local /home/$SERVICE_NAME/.local
COPY --from=builder /usr/sbin/gosu /usr/sbin/gosu

COPY entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh

# copy the content of the local src and config directory to the working directory
COPY config .
COPY src .

EXPOSE 5005

# command to run on container start
ENTRYPOINT ["/root/entrypoint.sh"]
CMD [ "python3", "./server.py" ]

LABEL org.label-schema.build-date=$BUILD_DATE 
LABEL org.opencontainers.image.authors="Stefan Allius <stefan.allius@t-online.de>"
LABEL org.opencontainers.image.source https://github.com/s-allius/tsun-gen3-proxy
LABEL org.opencontainers.image.description 'The "TSUN Gen3 Micro-Inverter" proxy enables a reliable connection between TSUN third generation inverters and an MQTT broker to integrate the inverter into typical home automations'
LABEL org.opencontainers.image.licenses="BSD-3-Clause"
LABEL org.opencontainers.image.vendor="Stefan Allius>"
