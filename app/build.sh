#!/bin/bash
# Usage: ./build.sh [dev|rc|rel]
# dev: development build
# rc: release candidate build
# rel: release build and push to ghcr.io
# Note: for release build, you need to set GHCR_TOKEN
# export GHCR_TOKEN=<YOUR_GITHUB_TOKEN> in your .zprofile
# see also: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry


set -e

BUILD_DATE=$(date -Iminutes)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
VERSION=$(git describe --tags --abbrev=0)
VERSION="${VERSION:1}"
arr=(${VERSION//./ })
MAJOR=${arr[0]}
IMAGE=tsun-gen3-proxy
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

if [[ $1 == debug ]] || [[ $1 == dev ]] ;then
IMAGE=docker.io/sallius/${IMAGE}
VERSION=${VERSION}+$1
elif [[ $1 == rc ]] || [[ $1 == rel ]] || [[ $1 == preview ]] ;then
IMAGE=ghcr.io/s-allius/${IMAGE}
else
echo argument missing!
echo try: $0 '[debug|dev|preview|rc|rel]'
exit 1
fi

if [[ $1 == debug ]] ;then
BUILD_ENV="dev"
else
BUILD_ENV="production"
fi

BUILD_CMD="buildx build --push --build-arg \"VERSION=${VERSION}\" --build-arg \"environment=${BUILD_ENV}\" --attest type=provenance,mode=max --attest type=sbom,generator=docker/scout-sbom-indexer:latest"
ARCH="--platform linux/amd64,linux/arm64,linux/arm/v7"
LABELS="--label \"org.opencontainers.image.created=${BUILD_DATE}\" --label \"org.opencontainers.image.version=${VERSION}\" --label \"org.opencontainers.image.revision=${BRANCH}\""

echo version: $VERSION  build-date: $BUILD_DATE   image: $IMAGE
if [[ $1 == debug ]];then
docker ${BUILD_CMD} ${ARCH} ${LABELS} --build-arg "LOG_LVL=DEBUG" -t ${IMAGE}:debug  app

elif [[ $1 == dev ]];then
docker ${BUILD_CMD} ${ARCH} ${LABELS} -t ${IMAGE}:dev app

elif [[ $1 == preview ]];then
echo 'login to ghcr.io'    
echo $GHCR_TOKEN | docker login ghcr.io -u s-allius --password-stdin
docker ${BUILD_CMD} ${ARCH} ${LABELS} -t ${IMAGE}:preview -t ${IMAGE}:${VERSION} app

elif [[ $1 == rc ]];then
echo 'login to ghcr.io'    
echo $GHCR_TOKEN | docker login ghcr.io -u s-allius --password-stdin
docker ${BUILD_CMD} ${ARCH} ${LABELS} -t ${IMAGE}:rc -t ${IMAGE}:${VERSION} app

elif [[ $1 == rel ]];then
echo 'login to ghcr.io'    
echo $GHCR_TOKEN | docker login ghcr.io -u s-allius --password-stdin
docker ${BUILD_CMD} ${ARCH} ${LABELS} --no-cache -t ${IMAGE}:latest -t ${IMAGE}:${MAJOR} -t ${IMAGE}:${VERSION} app
fi

echo -e "${BLUE} => checking docker-compose.yaml file${NC}"
docker-compose config -q
echo
echo -e "${GREEN}${BUILD_DATE} => Version: ${VERSION}${NC} finished"
echo
