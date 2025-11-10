ARG PYTHON_VER=3.10

FROM python:${PYTHON_VER} AS base

RUN pip install --upgrade pip && \
  pip install poetry

WORKDIR /local
# Poetry fails install without README.md being copied.
COPY pyproject.toml poetry.lock README.md /local/
COPY schema_enforcer /local/schema_enforcer

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# -----------------------------------------------------------------------------
# Defines stage with ansible installed
# -----------------------------------------------------------------------------
FROM base AS with_ansible
ARG ANSIBLE_PACKAGE=ansible-core
ARG ANSIBLE_VER=2.16.14
RUN pip install $ANSIBLE_PACKAGE==$ANSIBLE_VER
