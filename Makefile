.PHONY: build clean

# debug dev:
# 	$(MAKE) -C app $@

clean build:
	$(MAKE) -C ha_addon $@ 