#!make
include ../.env

SHELL = /bin/sh
IMAGE = tsun-gen3-proxy


# Folders
APP=.
SRC=$(APP)/src
# Folders for Babel translation
BABEL_INPUT_JINJA=$(SRC)/web/templates
BABEL_INPUT= $(foreach dir,$(BABEL_INPUT_JINJA),$(wildcard $(dir)/*.html)) \

BABEL_TRANSLATIONS=$(APP)/translations

export BUILD_DATE := ${shell date -Iminutes}
VERSION := $(shell cat $(APP)/.version)
export MAJOR  := $(shell echo $(VERSION) | cut -f1 -d.)

PUBLIC_URL := $(shell echo $(PUBLIC_CONTAINER_REGISTRY) | cut -f1 -d/)
PUBLIC_USER :=$(shell echo $(PUBLIC_CONTAINER_REGISTRY) | cut -f2 -d/)


dev debug:
	@echo version: $(VERSION)  build-date: $(BUILD_DATE)   image: $(PRIVAT_CONTAINER_REGISTRY)$(IMAGE)
	export VERSION=$(VERSION)-$@ && \
	export IMAGE=$(PRIVAT_CONTAINER_REGISTRY)$(IMAGE) && \
	docker buildx bake -f docker-bake.hcl $@

rc:
	@[ "${RC}" ] || ( echo ">> RC is not set"; exit 1 )
	@echo version: $(VERSION)  build-date: $(BUILD_DATE)   image: $(PUBLIC_CONTAINER_REGISTRY)$(IMAGE)
	@echo login at $(PUBLIC_URL) as $(PUBLIC_USER)
	@DO_LOGIN="$(shell echo $(PUBLIC_CR_KEY) | docker login $(PUBLIC_URL) -u $(PUBLIC_USER) --password-stdin)"
	export VERSION=$(VERSION)-$@$(RC) && \
	export IMAGE=$(PUBLIC_CONTAINER_REGISTRY)$(IMAGE) && \
	docker buildx bake -f docker-bake.hcl $@

preview rel:
	@echo version: $(VERSION)  build-date: $(BUILD_DATE)   image: $(PUBLIC_CONTAINER_REGISTRY)$(IMAGE)
	@echo login at $(PUBLIC_URL) as $(PUBLIC_USER)
	@DO_LOGIN="$(shell echo $(PUBLIC_CR_KEY) | docker login $(PUBLIC_URL) -u $(PUBLIC_USER) --password-stdin)"
	export VERSION=$(VERSION)-$@ && \
	export IMAGE=$(PUBLIC_CONTAINER_REGISTRY)$(IMAGE) && \
	docker buildx bake -f docker-bake.hcl $@

babel: $(BABEL_TRANSLATIONS)/de/LC_MESSAGES/messages.mo $(BABEL_TRANSLATIONS)/de/LC_MESSAGES/messages.po $(BABEL_TRANSLATIONS)/messages.pot

$(BABEL_TRANSLATIONS)/%.pot : $(SRC)/.babel.cfg $(BABEL_INPUT)
	@mkdir -p $(@D)
	@pybabel extract -F $< --project=$(IMAGE) --version=$(VERSION) -o $@ $(SRC)

$(BABEL_TRANSLATIONS)/%/LC_MESSAGES/messages.po : $(BABEL_TRANSLATIONS)/messages.pot
	@mkdir -p $(@D)
	@pybabel update  --init-missing -i $< -d $(BABEL_TRANSLATIONS) -l $*

$(BABEL_TRANSLATIONS)/%/LC_MESSAGES/messages.mo : $(BABEL_TRANSLATIONS)/%/LC_MESSAGES/messages.po
	@pybabel compile  -d $(BABEL_TRANSLATIONS) -l $*

.PHONY: babel debug dev preview rc rel
