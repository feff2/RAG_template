PYVERSION ?= 3.11.7
PIPVERSION ?= 2023.11.15

DOCKER = docker
DOCKER-COMPOSE = docker-compose
DOCKER_PLATFORM := linux/amd64

PROJECT_NAME := rag-template
LLM_SERVICE_IMAGE := $(PROJECT_NAME)_llm-service:latest
TRITON_CLIENT_IMAGE := $(PROJECT_NAME)_triton-client:latest

LLM_SERVICE_DOCKERFILE := ./deployment/docker/llm_service.Dockerfile
TRITON_CLIENT_DOCKERFILE := ./deployment/docker/triton_client.Dockerfile

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Availiable commandsfor work with docker:"
	@echo "  make docker-build-image-llm-service    - Build LLM service image"
	@echo "  make docker-build-image-triton-client  - Build Triton client image"
	@echo "  make build-all                         - Build all images"
	@echo "  make clean                             - Clean all images"
	@echo "  make list-images                       - Show builded images"


.PHONY: env
define ENV_SAMPLE
# переменная окружения "development" | "production"
ENVIRONMENT="development"

# индекс GPU, на которую усадим модель
GPU_INDEX=0
endef

export ENV_SAMPLE
env:
	$(call _info, $(SEP))
	$(call _info,"Try make .env")
	$(call _info, $(SEP))
	echo "$$ENV_SAMPLE" > .env;

.PHONY: shell
shell:
	pipenv shell

.PHONY: install-deps
install-deps:
	pipenv install --categories="packages dev-packages api inference-server"

.PHONY: pre-commit-install
pre-commit-install:
	pipenv run pre-commit install

.PHONY: create-requirements-txt-llm-service
create-requirements-txt-llm-service:
	pipenv requirements --categories="packages llm-service" > src/services/llm_service/requirements.txt

.PHONY: create-requirements-txt-triton-client
create-requirements-txt-triton-client:
	pipenv requirements --categories="packages triton-client" > src/services/triton_service/requirements.txt

.PHONY: create-requirements-txt-dev
create-requirements-txt-dev:
	pipenv requirements --categories="dev-packages" > requirements.txt

.PHONY: lint-check
lint-check:
	pipenv run ruff check src

.PHONY: format-check
format-check:
	pipenv run ruff format --check src

.PHONY: type-check
type-check:
	pipenv run pyright src

.PHONY: tests
tests:
	pipenv run pytest tests

.PHONY: lint-fix
lint-fix:
	pipenv run ruff --fix src && pipenv run ruff format src

.PHONY: docker-build-image-llm-service
docker-build-image-llm-service: create-requirements-txt-llm-service
	@echo "Build LLM service image..."
	$(DOCKER) build --platform $(DOCKER_PLATFORM) \
		-t $(LLM_SERVICE_IMAGE) \
		-f $(LLM_SERVICE_DOCKERFILE) \
		.
	@echo "LLM service image builded: $(LLM_SERVICE_IMAGE)"

.PHONY: docker-build-image-triton-client
docker-build-image-triton-client: create-requirements-txt-triton-client
	@echo "Build Triton client image..."
	$(DOCKER) build --platform $(DOCKER_PLATFORM) \
		-t $(TRITON_CLIENT_IMAGE) \
		-f $(TRITON_CLIENT_DOCKERFILE) \
		.
	@echo "Triton client image builded: $(TRITON_CLIENT_IMAGE)"

.PHONY: build-all
build-all: docker-build-image-llm-service docker-build-image-triton-client
	@echo "All builded Docker images"
	@echo "Images:"
	@echo "   - $(LLM_SERVICE_IMAGE)"
	@echo "   - $(TRITON_CLIENT_IMAGE)"

.PHONY: list-images
list-images:
	@echo "Builded images:"
	@$(DOCKER) images | grep $(PROJECT_NAME) || echo "📭 Образы не найдены"

.PHONY: clean
clean:
	@echo "Cleaning Docker images..."
	-$(DOCKER) rmi $(LLM_SERVICE_IMAGE) 2>/dev/null || echo "Образ LLM service не найден"
	-$(DOCKER) rmi $(TRITON_CLIENT_IMAGE) 2>/dev/null || echo "Образ Triton client не найден"
	@echo "Cleaning is completing"

.PHONY: run-llm-service
run-llm-service: docker-build-image-llm-service
	@echo "Start LLM service container..."
	$(DOCKER) run -it --rm -p 8000:8000 $(LLM_SERVICE_IMAGE)

.PHONY: run-triton-client
run-triton-client: docker-build-image-triton-client
	@echo "Start Triton client container..."
	$(DOCKER) run -it --rm $(TRITON_CLIENT_IMAGE)

.PHONY: install-deps-on-ci
install-deps-on-ci: create-requirements-txt-dev
	python -m pip --cache-dir ./pip-cache install -r requirements.txt

.PHONY: lint-check-ci
lint-check-ci:
	python -m ruff check src

.PHONY: format-check-ci
format-check-ci:
	python -m ruff format --check src

.PHONY: type-check-ci
type-check-ci:
	python -m pyright src

.PHONY: tests-ci
tests-ci:
	python -m pytest tests