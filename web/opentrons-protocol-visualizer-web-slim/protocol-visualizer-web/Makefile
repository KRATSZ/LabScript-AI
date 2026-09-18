.PHONY: setup setup-client dev-api dev-client

# Python API (uv). From monorepo root: `make -C protocol-visualizer-web setup`
setup:
	uv sync

setup-mcp:
	uv sync --extra mcp

setup-client:
	cd client && yarn install

dev-api:
	PV_CORS_ORIGINS=http://127.0.0.1:5177,http://localhost:5177 \
		uv run uvicorn protocol_visualizer_web.app:app --reload --host 127.0.0.1 --port 8765

dev-client:
	cd client && yarn dev
