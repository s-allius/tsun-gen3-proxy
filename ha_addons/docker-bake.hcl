variable "IMAGE" {
    default = "tsun-gen3-addon"
}
variable "VERSION" {
    default = "0.0.0"
}
variable "MAJOR" {
    default = "0"
}
variable "BUILD_DATE" {
    default = "dev"
}
variable "BRANCH" {
    default = ""
}
variable "DESCRIPTION" {
    default = "This proxy enables a reliable connection between TSUN third generation inverters (eg. TSOL MS600, MS800, MS2000) and an MQTT broker to integrate the inverter into typical home automations."
}

target "_common" {
  context = "ha_addon"
  dockerfile = "Dockerfile"
  args = {
    VERSION = "${VERSION}"
    environment = "production"
  }
  attest = [
    "type =provenance,mode=max",
    "type =sbom,generator=docker/scout-sbom-indexer:latest"
  ]
  annotations = [
    "index:io.hass.type=addon",
    "index:io.hass.arch=aarch64|amd64",
    "index,manifest-descriptor:org.opencontainers.image.title=TSUN-Proxy",
    "index,manifest-descriptor:org.opencontainers.image.authors=Stefan Allius",
    "index,manifest-descriptor:org.opencontainers.image.created=${BUILD_DATE}",
    "index,manifest-descriptor:org.opencontainers.image.version=${VERSION}",
    "index,manifest-descriptor:org.opencontainers.image.description=${DESCRIPTION}",
    "index:org.opencontainers.image.licenses=BSD-3-Clause",
    "index:org.opencontainers.image.source=https://github.com/s-allius/tsun-gen3-proxy/ha_addons/ha_addon",
  ]
  labels = {
    "io.hass.type" = "addon"
    "io.hass.arch" = "aarch64|amd64"
    "org.opencontainers.image.title" = "TSUN-Proxy"
    "org.opencontainers.image.authors" = "Stefan Allius"
    "org.opencontainers.image.created" = "${BUILD_DATE}"
    "org.opencontainers.image.version" = "${VERSION}"
    "org.opencontainers.image.description" = "${DESCRIPTION}"
    "org.opencontainers.image.licenses" = "BSD-3-Clause"
    "org.opencontainers.image.source" = "https://github.com/s-allius/tsun-gen3-proxy/ha_addonsha_addon"
  }
  output = [
    "type=image,push=true"
  ]

  no-cache = false
  platforms = ["linux/amd64", "linux/arm64"]
}

target "_debug" {
  args = {
    LOG_LVL = "DEBUG"
    environment = "dev"
  }
}
target "_prod" {
  args = {
  }
}
target "debug" {
  inherits = ["_common", "_debug"]
  tags = ["${IMAGE}:debug", "${IMAGE}:${VERSION}"]
}

target "dev" {
  inherits = ["_common"]
  tags = ["${IMAGE}:dev", "${IMAGE}:${VERSION}"]
}

target "preview" {
  inherits = ["_common", "_prod"]
  tags = ["${IMAGE}:preview", "${IMAGE}:${VERSION}"]
}

target "rc" {
  inherits = ["_common", "_prod"]
  tags = ["${IMAGE}:rc", "${IMAGE}:${VERSION}"]
  no-cache = true
}

target "rel" {
  inherits = ["_common", "_prod"]
  tags = ["${IMAGE}:latest", "${IMAGE}:${MAJOR}", "${IMAGE}:${VERSION}"]
  no-cache = true
}
