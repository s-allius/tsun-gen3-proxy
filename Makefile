.PHONY: build clean addon-dev addon-debug addon-rc debug dev preview rc rel

debug dev preview rc rel:
	$(MAKE) -C app $@

clean build:
	$(MAKE) -C ha_addons/ha_addon $@ 

addon-dev addon-debug addon-rc:
	$(MAKE) -C ha_addons/ha_addon $(patsubst addon-%,%,$@)

check-docker-compose:
	docker-compose config -q

