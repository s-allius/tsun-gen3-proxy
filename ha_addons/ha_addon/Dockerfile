
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

ARG BUILD_FROM="ghcr.io/hassio-addons/base:stable"
FROM $BUILD_FROM AS base

# Installiere Python, pip und virtuelle Umgebungstools
# RUN apk add --no-cache python3 py3-pip py3-virtualenv
RUN apk add --no-cache python3 py3-pip

#######################
# 2 Modify Image      #
#######################
FROM base AS builder
COPY rootfs/requirements.txt /root/

RUN apk add --no-cache build-base && \
    python -m pip install --no-cache-dir -U pip wheel && \
    python -OO -m pip wheel --no-cache-dir --wheel-dir=/root/wheels -r /root/requirements.txt




#######################
# 3 Install apps      #
#######################
FROM base AS runtime


# Installiere Python, pip und virtuelle Umgebungstools
# RUN apk add --no-cache python3 py3-pip py3-virtualenv

# Erstelle ein virtuelles Umfeld und aktiviere es
# RUN python3 -m venv /opt/venv

# RUN . /opt/venv/bin/activate

# Stelle sicher, dass das Add-on das virtuelle Umfeld nutzt
# ENV PATH="/opt/venv/bin:$PATH"



#######################
# 4 Install libraries #
#######################


# install the requirements from the wheels packages from the builder stage 
# and unistall python packages and alpine package manger to reduce attack surface

# --no-cache-dir ??
COPY --from=builder /root/wheels /root/wheels
RUN python -m pip install --no-cache --no-index /root/wheels/* && \
    rm -rf /root/wheels && \
    python -m pip uninstall --yes wheel pip && \
    apk --purge del apk-tools


#######################
# 5 copy data         #
#######################


# Add rootfs
COPY rootfs/ /

# make run.sh executable
RUN chmod a+x /run.sh



#######################
# 6 run app           #
#######################

ARG SERVICE_NAME
ARG VERSION
ENV SERVICE_NAME=${SERVICE_NAME}

RUN echo ${VERSION} > /proxy-version.txt

# command to run on container start
CMD [ "/run.sh" ]



#######################

