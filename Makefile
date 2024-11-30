.PHONY: build clean addon-dev

# debug dev:
# 	$(MAKE) -C app $@

clean build addon-dev:
	$(MAKE) -C ha_addon $@ 