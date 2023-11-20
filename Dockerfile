# syntax=docker.io/docker/dockerfile:1
# vim:set ft=dockerfile:
#
# Hadolint ignores:
#   DL3042: Avoid use of cache directory with pip

FROM python:3.12-slim

#
# Set the RUN shell to bash, and set pipefail
#
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN mkdir /app
WORKDIR /app

#
# Install git
#
RUN --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    rm --force /etc/apt/apt.conf.d/docker-clean \
 && apt-get update \
 && apt-get install \
        -y \
        --no-install-recommends \
        git=1:2.39.2-1.1

#
# Set git to trust /mnt
#
RUN git config \
        --global \
        --add safe.directory /mnt

#
# Install poetry, and then install the dependencies
#
# hadolint ignore=DL3042
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

ENTRYPOINT ["python", "/app/run.py", "--path", "/mnt/"]
