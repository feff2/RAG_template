PYVERSION ?= 3.10.13
PIPVERSION ?= 2023.11.15

DOCKER = docker
DOCKER-COMPOSE = docker-compose
DOCKER_PLATFORM := linux/amd64

PROJECT_NAME := rag-template

API_GATEWAY_IMAGE := $(PROJECT_NAME)_api_gateway:latest
API_GATEWAY_DOCKERFILE := ./deployment/docker/api_gateway.Dockerfile

.PHONY: docker-build-image-api-gateway
docker-build-image-api-gateway:
	@echo "Build api_gateway image..."
	$(DOCKER) build --platform $(DOCKER_PLATFORM) \
		-t $(API_GATEWAY_IMAGE) \
		-f $(API_GATEWAY_DOCKERFILE) \
		.
	@echo "Api gateway image built: $(API_GATEWAY_IMAGE)"

.PHONY: run-api-gateway
run-api-gateway: docker-build-image-api-gateway
	@echo "Start API gateway container..."
	$(DOCKER) run -it --rm -p 8080:8080 $(API_GATEWAY_IMAGE)
