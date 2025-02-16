#!make
include ../.env

.PHONY: debug dev build clean rootfs repro rc rel

SHELL = /bin/sh
JINJA = jinja2
IMAGE = tsun-gen3-addon


# Source folders for building the local add-on
SRC=../app
SRC_PROXY=$(SRC)/src
CNF_PROXY=$(SRC)/config

# Target folders for building the local add-on and the docker container
ADDON_PATH = ha_addon
DST=$(ADDON_PATH)/rootfs
DST_PROXY=$(DST)/home/proxy

# base director of the add-on repro for installing the add-on git repros
INST_BASE=../../ha-addons/ha-addons

# Template folder for build the config.yaml variants 
TEMPL=templates

# help variable STAGE determine the target to build
dev: STAGE=dev
debug : STAGE=debug
rc :  STAGE=rc
rel : STAGE=rel


export BUILD_DATE := ${shell date -Iminutes}
VERSION := $(shell cat $(SRC)/.version)
export MAJOR  := $(shell echo $(VERSION) | cut -f1 -d.)

PUBLIC_URL := $(shell echo $(PUBLIC_CONTAINER_REGISTRY) | cut -f1 -d/)
PUBLIC_USER :=$(shell echo $(PUBLIC_CONTAINER_REGISTRY) | cut -f2 -d/)


dev debug: local_add_on repro
	@echo version: $(VERSION)  build-date: $(BUILD_DATE)   image: $(PRIVAT_CONTAINER_REGISTRY)$(IMAGE)
	export VERSION=$(VERSION)-$@ && \
	export IMAGE=$(PRIVAT_CONTAINER_REGISTRY)$(IMAGE) && \
	docker buildx bake -f docker-bake.hcl $@

rc rel: local_add_on repro
	@echo version: $(VERSION)  build-date: $(BUILD_DATE)   image: $(PUBLIC_CONTAINER_REGISTRY)$(IMAGE)
	@echo login at $(PUBLIC_URL) as $(PUBLIC_USER)
	@DO_LOGIN="$(shell echo $(PUBLIC_CR_KEY) | docker login $(PUBLIC_URL) -u $(PUBLIC_USER) --password-stdin)"
	export VERSION=$(VERSION)-$@ && \
	export IMAGE=$(PUBLIC_CONTAINER_REGISTRY)$(IMAGE) && \
	docker buildx bake -f docker-bake.hcl $@

clean:
	rm -r -f $(DST_PROXY)
	rm -f $(DST)/requirements.txt
	rm -f $(ADDON_PATH)/config.yaml
	rm -f $(TEMPL)/.data.json
	docker logout ghcr.io

#############
# Build the local add-on with a rootfs and config.yaml
# The rootfs is needed to build the add-on Docker container 
# 
local_add_on: rootfs $(ADDON_PATH)/config.yaml

# collect source files 
SRC_FILES := $(wildcard $(SRC_PROXY)/*.py)\
 $(wildcard $(SRC_PROXY)/*.ini)\
 $(wildcard $(SRC_PROXY)/cnf/*.py)\
 $(wildcard $(SRC_PROXY)/cnf/*.toml)\
 $(wildcard $(SRC_PROXY)/gen3/*.py)\
 $(wildcard $(SRC_PROXY)/gen3plus/*.py)
CNF_FILES := $(wildcard $(CNF_PROXY)/*.toml)

# determine destination files
TARGET_FILES = $(SRC_FILES:$(SRC_PROXY)/%=$(DST_PROXY)/%)
CONFIG_FILES = $(CNF_FILES:$(CNF_PROXY)/%=$(DST_PROXY)/%)

rootfs: $(TARGET_FILES) $(CONFIG_FILES) $(DST)/requirements.txt

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

$(ADDON_PATH)/%.yaml: $(TEMPL)/%.jinja $(TEMPL)/.data.json
	$(JINJA) --strict -D AppVersion=$(VERSION) --format=json $^ -o $@

$(TEMPL)/.data.json: FORCE
	rsync --checksum $(TEMPL)/$(STAGE)_data.json $@

FORCE : ;


#############
# Build repository for Home Assistant Add-On
# 

repro_files = DOCS.md README.md icon.png logo.png translations/de.yaml translations/en.yaml rootfs/run.sh
repro_root = CHANGELOG.md LICENSE.md
repro_templates = config.yaml
repro_subdirs = translations rootfs
# repro_vers = debug dev rc rel
repro_vers = $(STAGE)

repro_all_files := $(foreach dir,$(repro_vers), $(foreach file,$(repro_files),$(INST_BASE)/ha_addon_$(dir)/$(file)))
repro_root_files := $(foreach dir,$(repro_vers), $(foreach file,$(repro_root),$(INST_BASE)/ha_addon_$(dir)/$(file)))
repro_all_templates := $(foreach dir,$(repro_vers), $(foreach file,$(repro_templates),$(INST_BASE)/ha_addon_$(dir)/$(file)))
repro_all_subdirs := $(foreach dir,$(repro_vers), $(foreach file,$(repro_subdirs),$(INST_BASE)/ha_addon_$(dir)/$(file)))

repro: $(repro_all_subdirs)  $(repro_all_templates) $(repro_all_files) $(repro_root_files)

$(repro_all_subdirs) :
	mkdir -p $@

$(repro_all_templates) : $(INST_BASE)/ha_addon_%/config.yaml: $(TEMPL)/config.jinja $(TEMPL)/%_data.json $(SRC)/.version
	$(JINJA) --strict -D AppVersion=$(VERSION)-$* $< $(filter %.json,$^) -o $@

$(repro_root_files) : %/CHANGELOG.md : ../CHANGELOG.md
	cp $< $@
$(repro_root_files) : %/LICENSE.md : ../LICENSE.md
	cp $< $@

$(filter $(INST_BASE)/ha_addon_debug/%,$(repro_all_files)) : $(INST_BASE)/ha_addon_debug/% : ha_addon/%
	cp $< $@
$(filter $(INST_BASE)/ha_addon_dev/%,$(repro_all_files)) : $(INST_BASE)/ha_addon_dev/% : ha_addon/%
	cp $< $@
$(filter $(INST_BASE)/ha_addon_rc/%,$(repro_all_files)) : $(INST_BASE)/ha_addon_rc/% : ha_addon/%
	cp $< $@
$(filter $(INST_BASE)/ha_addon_rel/%,$(repro_all_files)) : $(INST_BASE)/ha_addon_rel/% : ha_addon/%
	cp $< $@
