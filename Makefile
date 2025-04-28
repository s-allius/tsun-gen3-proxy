.PHONY: build babel clean addon-dev addon-debug addon-rc addon-rel debug dev preview rc rel check-docker-compose install

babel:
	$(MAKE) -C app $@

build:
	$(MAKE) -C ha_addons $@ 

clean build:
	$(MAKE) -C app $@
	$(MAKE) -C ha_addons $@ 

debug dev preview rc rel:
	$(MAKE) -C app babel
	$(MAKE) -C app $@

addon-dev addon-debug addon-rc addon-rel:
	$(MAKE) -C app babel
	$(MAKE) -C ha_addons $(patsubst addon-%,%,$@)

check-docker-compose:
	docker-compose config -q

install:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements-test.txt