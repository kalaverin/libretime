set dotenv-load := true
set positional-arguments := true

DATETIME := `TZ=UTC date '+%Y-%m-%d %H:%M:%S'`
DOCKER_TAG := env('DOCKER_TAG', 'libretime/development')
BASE_IMAGE := env('BASE_IMAGE', 'ghcr.io/astral-sh/uv:python3.13-bookworm-slim')

UV_INDEX_PRIVATE_USERNAME := env('UV_INDEX_PRIVATE_USERNAME', '__token__')
UV_INDEX_PRIVATE_PASSWORD := env('UV_INDEX_PRIVATE_PASSWORD', '')

default:
    @just --list

# clean bytecode and cache files, also useful to reset state of linters and type checkers
[group('maintenance')]
clean:
    @rm -rf .*_cache/
    @find . -type d -name "__pycache__" -exec rm -rf {} +
    @find . -type f -name "*.pyc" -exec rm -f {} +

# upgrade dependencies graph
[group('packaging')]
upgrade:
    @echo "upgrading mise dependencies.."
    @mise upgrade \
        --quiet \
        --yes \

    @echo "updating pre-commit hooks.."
    @uv run --quiet \
    pre-commit autoupdate \
        --config etc/pre-commit.yaml

    @echo "upgrading project (with development group) dependencies.."
    @uv sync \
        --refresh \
        --upgrade \
        --all-packages \
        --group development

    @echo "installed dependencies after upgrade:"
    @uv pip list

    @echo "locking updated dependencies.."
    @uv lock --upgrade

# build docker image
[group('packaging')]
dock:
    @uv lock --quiet
    docker buildx build --load \
        --build-arg BASE_IMAGE="{{BASE_IMAGE}}" \
        --build-arg UV_INDEX_PRIVATE_USERNAME="{{UV_INDEX_PRIVATE_USERNAME}}" \
        --build-arg UV_INDEX_PRIVATE_PASSWORD="{{UV_INDEX_PRIVATE_PASSWORD}}" \
        -t "{{DOCKER_TAG}}" .

# just tests
[group('project')]
test:
    @uv run \
    pytest \
        -svvv \
        -rs \
        --cov-report term-missing \
        --cov app \
        --cov src/sdk

# development method of running the application
[group('project')]
develop:
    @cd .. && cd - && \
    uv run development.py

# add development packages to environment when skipped
[group('maintenance')]
_development_packages:
    @uv sync \
        --quiet \
        --all-packages \
        --group development
