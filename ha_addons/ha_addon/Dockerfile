
############################################################################
#
# TSUN Proxy
# Homeassistant Add-on
# 
# based on https://github.com/s-allius/tsun-gen3-proxy/tree/main
#
############################################################################


######################
# 1 Build Image      #
######################

ARG BUILD_FROM="ghcr.io/hassio-addons/base:stable"
FROM $BUILD_FROM


#######################
# 2 Modify Image      #
#######################




#######################
# 3 Install apps      #
#######################



# Installiere Python, pip und virtuelle Umgebungstools
RUN apk add --no-cache python3 py3-pip py3-virtualenv

# Erstelle ein virtuelles Umfeld und aktiviere es
RUN python3 -m venv /opt/venv

RUN . /opt/venv/bin/activate

# Stelle sicher, dass das Add-on das virtuelle Umfeld nutzt
ENV PATH="/opt/venv/bin:$PATH"



#######################
# 4 Install libraries #
#######################


# Kopiere die requirements.txt Datei in das Image
COPY rootfs/requirements.txt /tmp/requirements.txt

#  installiere die Pakete aus requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


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

