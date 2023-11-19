# syntax=docker.io/docker/dockerfile:1
# vim:set ft=dockerfile:

FROM python:3.12-slim

RUN mkdir /app
WORKDIR /app

RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      git

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pypoetry \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=poetry.lock,target=poetry.lock \
    pip install poetry==1.7.0 \
 && poetry config virtualenvs.create false \
 && poetry export --format=requirements.txt \
                  --without-hashes \
                  --with main \
  | pip install --requirement /dev/stdin

COPY delta/ /app

ENTRYPOINT ["python", "/app/run.py", "--path /mnt/"]
