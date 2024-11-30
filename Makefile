.PHONY: build clean addon-dev addon-debug sddon-rc

# debug dev:
# 	$(MAKE) -C app $@

clean build:
	$(MAKE) -C ha_addons/ha_addon $@ 

addon-dev addon-debug addon-rc:
	$(MAKE) -C ha_addons/ha_addon $(patsubst addon-%,%,$@)