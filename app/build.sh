#!/bin/bash

set -e

BUILD_DATE=$(date -Iminutes)
VERSION=$(git describe --tags --abbrev=0)
VERSION="${VERSION:1}"
arr=(${VERSION//./ })
MAJOR=${arr[0]}
IMAGE=tsun-gen3-proxy

if [[ $1 == dev ]];then
IMAGE=docker.io/sallius/${IMAGE}
VERSION=${VERSION}-dev
elif [[ $1 == rel ]];then
IMAGE=ghcr.io/s-allius/${IMAGE}
else
echo argument missing!
echo try: $0 '[dev|rel]'
exit 1
fi

echo version: $VERSION  build-date: $BUILD_DATE   image: $IMAGE
if [[ $1 == dev ]];then
docker build --build-arg "VERSION=${VERSION}" --label "org.label-schema.build-date=${BUILD_DATE}" --label "org.opencontainers.image.version=${VERSION}" -t ${IMAGE}:latest app
elif [[ $1 == rel ]];then
docker build --no-cache --build-arg "VERSION=${VERSION}" --label "org.label-schema.build-date=${BUILD_DATE}" --label "org.opencontainers.image.version=${VERSION}" -t ${IMAGE}:latest -t ${IMAGE}:${MAJOR} -t ${IMAGE}:${VERSION} app
docker push ghcr.io/s-allius/tsun-gen3-proxy:latest
docker push ghcr.io/s-allius/tsun-gen3-proxy:${MAJOR}
docker push ghcr.io/s-allius/tsun-gen3-proxy:${VERSION}
fi