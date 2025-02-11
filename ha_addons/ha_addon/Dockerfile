
############################################################################
#
# TSUN Proxy
# Homeassistant Add-on
# 
# based on https://github.com/s-allius/tsun-gen3-proxy/tree/main
#
############################################################################


######################
# 1 Build Base Image #
######################

ARG BUILD_FROM="ghcr.io/hassio-addons/base:17.1.0"
# hadolint ignore=DL3006
FROM $BUILD_FROM AS base

# Installiere Python, pip und virtuelle Umgebungstools
RUN apk add --no-cache python3=3.12.8-r1 py3-pip=24.3.1-r0 && \
    python -m venv /opt/venv && \
    . /opt/venv/bin/activate

ENV PATH="/opt/venv/bin:$PATH"



#######################
# 2 Build wheel       #
#######################
FROM base AS builder

COPY rootfs/requirements.txt /root/

RUN apk add --no-cache build-base=0.5-r3 && \
    python -m pip install --no-cache-dir wheel==0.45.1 && \
    python -OO -m pip wheel --no-cache-dir --wheel-dir=/root/wheels -r /root/requirements.txt




#######################
# 3 Build runtime     #
#######################
FROM base AS runtime

ARG SERVICE_NAME
ARG VERSION
ENV SERVICE_NAME=${SERVICE_NAME}



#######################
# 4 Install libraries #
#######################

# install the requirements from the wheels packages from the builder stage 
# and unistall python packages and alpine package manger to reduce attack surface

COPY --from=builder /root/wheels /root/wheels
RUN python -m pip install --no-cache-dir --no-cache --no-index /root/wheels/* && \
    rm -rf /root/wheels && \
    python -m pip uninstall --yes wheel pip && \
    apk --purge del apk-tools


#######################
# 5 copy data         #
#######################

COPY rootfs/ /



#######################
# 6 run app           #
#######################

# make run.sh executable
RUN chmod a+x /run.sh && \
    echo ${VERSION} > /proxy-version.txt

# command to run on container start
CMD [ "/run.sh" ]



#######################

