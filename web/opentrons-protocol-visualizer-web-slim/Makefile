.PHONY: setup setup-api setup-client dev-api dev-client

setup:
	yarn install
	make -C api setup
	make -C protocol-visualizer-web setup
	make -C protocol-visualizer-web setup-client

setup-api:
	make -C api setup

setup-client:
	make -C protocol-visualizer-web setup-client

dev-api:
	make -C protocol-visualizer-web dev-api

dev-client:
	make -C protocol-visualizer-web dev-client
