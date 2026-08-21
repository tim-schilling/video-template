set dotenv-load := true

default:
    just --list

install:
    uv sync

up:
    docker compose up -d

down:
    docker compose down

manage *ARGS:
    uv run manage.py {{ ARGS }}

migrate:
    just manage migrate

makemigrations:
    just manage makemigrations

collectstatic:
    just manage collectstatic --noinput

run:
    just manage runserver

server:
    uv run manage.py server web

worker:
    uv run manage.py worker worker

test:
    uv run pytest

lint:
    uv run pre-commit run --all-files

format:
    uv run ruff format .

shell:
    just manage shell

superuser:
    just manage createsuperuser

requirements:
    uv export --no-dev --no-hashes --format requirements-txt --output-file requirements.txt

deploy-pythonanywhere-plan:
    just requirements
    op run --env-file=.env.pythonanywhere -- uv run manage.py deploy

deploy-pythonanywhere:
    just requirements
    op run --env-file=.env.pythonanywhere -- uv run manage.py deploy --automate-all
