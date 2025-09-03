PYVERSION ?= 3.11.7
PIPVERSION ?= 2023.11.15

DOCKER = docker
DOCKER-COMPOSE = docker-compose

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

.PHONY: create-requirements-txt-api
create-requirements-txt-api:
	pipenv requirements --categories="packages api" > requirements-api.txt

.PHONY: create-requirements-txt-inference-server
create-requirements-txt-inference-server:
	pipenv requirements --categories="packages inference-server" > requirements-inference-server.txt

.PHONY: create-requirements-txt-dev
create-requirements-txt-dev:
	pipenv requirements --categories="dev-packages" > requirements.txt

.PHONY: lint-check
lint-check:
	pipenv run ruff check src

docker-build-deps:
	$(DOCKER) build --platform linux/amd64 \
		--build-arg PIPVERSION=${PIPVERSION} \
		-t ml-generation-comments_deps:latest \
		-f ./deployment/docker/dev/deps.Dockerfile \
		.

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

.PHONY: docker-build-image-inference-server
docker-build-image-inference-server: create-requirements-txt-inference-server
	$(DOCKER) build --platform linux/amd64 \
		-t ml-generation-comments_inference-server:latest \
		-f ./deployment/docker/inference_server.Dockerfile \
		.

.PHONY: docker-build-image-api
docker-build-image-api: create-requirements-txt-api
	$(DOCKER) build --platform linux/amd64 \
		--target runtime \
		-t ml-generation-comments_api:latest \
		-f ./deployment/docker/api.Dockerfile \
		.

.PHONY: docker-run-deps
docker-run-deps: docker-build-deps
	$(DOCKER) run \
		--platform linux/amd64 \
		--entrypoint /bin/bash \
		-v ./:/code \
		-it ml-generation-comments_deps:latest

# и pipenv install --dev и т.п.

.PHONY: docker-run-apps
docker-run-apps: docker-build-image-api docker-build-image-inference-server
	$(DOCKER-COMPOSE) -f ./deployment/docker-compose/docker-compose.dev.yml up -d

.PHONY: docker-stop-apps
docker-stop-apps:
	$(DOCKER-COMPOSE) -f ./deployment/docker-compose/docker-compose.dev.yml down -v

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