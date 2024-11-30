.PHONY: build clean addon-dev addon-debug

# debug dev:
# 	$(MAKE) -C app $@

clean build:
	$(MAKE) -C ha_addon $@ 

addon-dev addon-debug:
	$(MAKE) -C ha_addon $(patsubst addon-%,%,$@)