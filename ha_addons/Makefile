#!make
include ../.env

SHELL = /bin/sh
IMAGE = tsun-gen3-addon



# Folders
SRC=../app
SRC_PROXY=$(SRC)/src
CNF_PROXY=$(SRC)/config

ADDON_PATH = ha_addon
DST=$(ADDON_PATH)/rootfs
DST_PROXY=$(DST)/home/proxy

INST_BASE=../../ha-addons/ha-addons

JINJA=jinja2
TEMPL=templates

# collect source files 
SRC_FILES := $(wildcard $(SRC_PROXY)/*.py)\
 $(wildcard $(SRC_PROXY)/*.ini)\
 $(wildcard $(SRC_PROXY)/cnf/*.py)\
 $(wildcard $(SRC_PROXY)/gen3/*.py)\
 $(wildcard $(SRC_PROXY)/gen3plus/*.py)
CNF_FILES := $(wildcard $(CNF_PROXY)/*.toml)

# determine destination files
TARGET_FILES = $(SRC_FILES:$(SRC_PROXY)/%=$(DST_PROXY)/%)
CONFIG_FILES = $(CNF_FILES:$(CNF_PROXY)/%=$(DST_PROXY)/%)

export BUILD_DATE := ${shell date -Iminutes}
VERSION := $(shell cat $(SRC)/.version)
export MAJOR  := $(shell echo $(VERSION) | cut -f1 -d.)

PUBLIC_URL := $(shell echo $(PUBLIC_CONTAINER_REGISTRY) | cut -f1 -d/)
PUBLIC_USER :=$(shell echo $(PUBLIC_CONTAINER_REGISTRY) | cut -f2 -d/)

STAGE=dev
INST=$(INST_BASE)/ha_addon_dev
debug : STAGE=debug
debug : INST=$(INST_BASE)/ha_addon_debug
rc :  STAGE=rc
rc :  INST=$(INST_BASE)/ha_addon_rc
rel : STAGE=rel
rel : INST=$(INST_BASE)/ha_addon

dev debug: build
	@echo version: $(VERSION)  build-date: $(BUILD_DATE)   image: $(PRIVAT_CONTAINER_REGISTRY)$(IMAGE)
	export VERSION=$(VERSION)-$@ && \
	export IMAGE=$(PRIVAT_CONTAINER_REGISTRY)$(IMAGE) && \
	docker buildx bake -f docker-bake.hcl $@

rc: build
	@echo version: $(VERSION)  build-date: $(BUILD_DATE)   image: $(PUBLIC_CONTAINER_REGISTRY)$(IMAGE)
	@echo login at $(PUBLIC_URL) as $(PUBLIC_USER)
	@DO_LOGIN="$(shell echo $(PUBLIC_CR_KEY) | docker login $(PUBLIC_URL) -u $(PUBLIC_USER) --password-stdin)"
	export VERSION=$(VERSION)-$@ && \
	export IMAGE=$(PUBLIC_CONTAINER_REGISTRY)$(IMAGE) && \
	docker buildx bake -f docker-bake.hcl $@


build: rootfs $(ADDON_PATH)/config.yaml

clean:
	rm -r -f $(DST_PROXY)
	rm -f $(DST)/requirements.txt
	rm -f $(ADDON_PATH)/config.yaml
	rm -f $(TEMPL)/.data.json

rootfs: $(TARGET_FILES) $(CONFIG_FILES) $(DST)/requirements.txt


.PHONY: debug dev build clean rootfs 

$(ADDON_PATH)/%.yaml: $(TEMPL)/%.jinja $(TEMPL)/.data.json
	$(JINJA) --strict --format=json $^ -o $@
	mkdir -p $(INST)
	cp $@ $(INST)/$(@F)

$(TEMPL)/.data.json: FORCE
	rsync --checksum $(TEMPL)/$(STAGE)_data.json $@

FORCE : ;

$(CONFIG_FILES): $(DST_PROXY)/% : $(CNF_PROXY)/%
	@echo Copy $< to $@
	@mkdir -p $(@D)
	@cp $< $@

$(TARGET_FILES): $(DST_PROXY)/% : $(SRC_PROXY)/%
	@echo Copy $< to $@
	@mkdir -p $(@D)
	@cp $< $@

$(DST)/requirements.txt : $(SRC)/requirements.txt
	@echo Copy $< to $@
	@cp $< $@
