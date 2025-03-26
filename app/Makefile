#!make
include ../.env

SHELL = /bin/sh
IMAGE = tsun-gen3-proxy


# Folders
SRC=.

export BUILD_DATE := ${shell date -Iminutes}
VERSION := $(shell cat $(SRC)/.version)
export MAJOR  := $(shell echo $(VERSION) | cut -f1 -d.)

PUBLIC_URL := $(shell echo $(PUBLIC_CONTAINER_REGISTRY) | cut -f1 -d/)
PUBLIC_USER :=$(shell echo $(PUBLIC_CONTAINER_REGISTRY) | cut -f2 -d/)


dev debug:
	@echo version: $(VERSION)  build-date: $(BUILD_DATE)   image: $(PRIVAT_CONTAINER_REGISTRY)$(IMAGE)
	export VERSION=$(VERSION)-$@ && \
	export IMAGE=$(PRIVAT_CONTAINER_REGISTRY)$(IMAGE) && \
	docker buildx bake -f docker-bake.hcl $@

preview rc rel:
	@echo version: $(VERSION)  build-date: $(BUILD_DATE)   image: $(PUBLIC_CONTAINER_REGISTRY)$(IMAGE)
	@echo login at $(PUBLIC_URL) as $(PUBLIC_USER)
	@DO_LOGIN="$(shell echo $(PUBLIC_CR_KEY) | docker login $(PUBLIC_URL) -u $(PUBLIC_USER) --password-stdin)"
	export VERSION=$(VERSION)-$@ && \
	export IMAGE=$(PUBLIC_CONTAINER_REGISTRY)$(IMAGE) && \
	docker buildx bake -f docker-bake.hcl $@


.PHONY: debug dev preview rc rel
