.PHONY: help build babel clean addon-dev addon-debug addon-rc addon-rel debug dev preview rc rel check-docker-compose install

help: ## show help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[$$()% a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

babel:            ## build language files
	$(MAKE) -C app $@

build:
	$(MAKE) -C ha_addons $@ 

clean:             ## delete all built files
	$(MAKE) -C app $@
	$(MAKE) -C ha_addons $@ 

debug dev preview rc rel:  ## build docker container in <dev|debg|rc|rel> version
	$(MAKE) -C app babel
	$(MAKE) -C app $@

addon-dev addon-debug addon-rc addon-rel: ## build HA add-on in <dev|debg|rc|rel> version
	$(MAKE) -C app babel
	$(MAKE) -C ha_addons $(patsubst addon-%,%,$@)

check-docker-compose: ## check the docker-compose file
	docker-compose config -q

PY_VER := $(shell cat .python-version)

install:           ## install requirements into the pyenv and switch to proper venv
	@pyenv local $(PY_VER) || { pyenv install $(PY_VER) && pyenv local $(PY_VER) || exit 1; }
	@pyenv exec pip install --upgrade pip
	@pyenv exec pip install -r requirements.txt
	@pyenv exec pip install -r requirements-test.txt
	pyenv exec python --version

run:  ## run proxy locally out of the actual venv
	pyenv exec python app/src/server.py -c /app/src/cnf