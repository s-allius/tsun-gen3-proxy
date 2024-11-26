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


if [[ $1 == addon ]] ;then
echo Prepare AddOn 
ADDON_PATH="ha_addon/rootfs/home/proxy"
SRC_PATH="app/src"
CNF_PATH="app/config"

mkdir -p $ADDON_PATH
rm -rf ${ADDON_PATH}/*
mkdir $ADDON_PATH/gen3 $ADDON_PATH/gen3plus

cp -a ${CNF_PATH}/*.toml ${ADDON_PATH}
cp -a ${SRC_PATH}/*.ini ${ADDON_PATH}
cp -a ${SRC_PATH}/*.py ${ADDON_PATH}
cp -a ${SRC_PATH}/gen3/*.py ${ADDON_PATH}/gen3
cp -a ${SRC_PATH}/gen3plus/*.py ${ADDON_PATH}/gen3plus

exit 0
fi

if [[ $1 == debug ]] || [[ $1 == dev ]] ;then
IMAGE=docker.io/sallius/${IMAGE}
VERSION=${VERSION}+$1
elif [[ $1 == rc ]] || [[ $1 == rel ]] || [[ $1 == preview ]] ;then
IMAGE=ghcr.io/s-allius/${IMAGE}
echo 'login to ghcr.io'    
echo $GHCR_TOKEN | docker login ghcr.io -u s-allius --password-stdin
else
echo argument missing!
echo try: $0 '[addon|debug|dev|preview|rc|rel]'
exit 1
fi

export IMAGE
export VERSION
export BUILD_DATE
export BRANCH
export MAJOR

echo version: $VERSION  build-date: $BUILD_DATE   image: $IMAGE
docker buildx bake -f app/docker-bake.hcl $1

echo -e "${BLUE} => checking docker-compose.yaml file${NC}"
docker-compose config -q
echo
echo -e "${GREEN}${BUILD_DATE} => Version: ${VERSION}${NC} finished"
echo
