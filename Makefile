.PHONY: build babel clean addon-dev addon-debug addon-rc addon-rel debug dev preview rc rel check-docker-compose install

babel debug dev preview rc rel:
	$(MAKE) -C app $@

clean build:
	$(MAKE) -C ha_addons $@ 

addon-dev addon-debug addon-rc addon-rel:
	$(MAKE) -C app babel
	$(MAKE) -C ha_addons $(patsubst addon-%,%,$@)

check-docker-compose:
	docker-compose config -q

install:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements-test.txt