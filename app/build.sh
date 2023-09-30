#!/bin/sh

BUILD_DATE=$(date -Iminutes)
VERSION=$(git describe --tags --abbrev=0)
VERSION="${VERSION:1}"
arr=(${VERSION//./ })
MAJOR=${arr[0]}
echo version: $VERSION  build-date: $BUILD_DATE
exec docker build --label "org.label-schema.build-date=${BUILD_DATE}" --label "org.opencontainers.image.version=${VERSION}" \
 -t "ghcr.io/s-allius/tsun-gen3-proxy:latest" -t "ghcr.io/s-allius/tsun-gen3-proxy:${MAJOR}" -t "ghcr.io/s-allius/tsun-gen3-proxy:${VERSION}" app
docker push ghcr.io/s-allius/tsun-gen3-proxy:latest
docker push ghcr.io/s-allius/tsun-gen3-proxy:${MAJOR}
docker push ghcr.io/s-allius/tsun-gen3-proxy:${VERSION}