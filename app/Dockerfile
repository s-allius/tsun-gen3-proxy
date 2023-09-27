ARG SERVICE_NAME="tsun-proxy"
ARG UID=1000

# set base image (host OS)
FROM python:3.11-slim-bookworm AS builder

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
ENV SERVICE_NAME=$SERVICE_NAME
ENV UID=$UID

RUN addgroup --gid 1000 $SERVICE_NAME && \
    adduser --ingroup $SERVICE_NAME --shell /bin/false --disabled-password --uid $UID $SERVICE_NAME && \
    mkdir -p /home/$SERVICE_NAME/log && \
    mkdir -p /home/$SERVICE_NAME/config && \
    chown --recursive $SERVICE_NAME:$SERVICE_NAME /home/$SERVICE_NAME

# set the working directory in the container
WORKDIR /home/$SERVICE_NAME
USER $SERVICE_NAME

# copy only the dependencies installation from the 1st stage image
COPY --from=builder --chown=$SERVICE_NAME:$SERVICE_NAME /root/.local /home/$SERVICE_NAME/.local

# copy the content of the local src and config directory to the working directory
COPY --chown=$SERVICE_NAME:$SERVICE_NAME config .
COPY --chown=$SERVICE_NAME:$SERVICE_NAME src .

# update PATH environment variable
ENV HOME=/home/$SERVICE_NAME
ENV PATH=/home/$SERVICE_NAME/.local:$PATH

EXPOSE 5005

LABEL de.allius.image.authors="Stefan Allius <stefan.allius@t-online.de>"

# command to run on container start
CMD [ "python3", "./server.py" ]