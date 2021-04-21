ARG PYTHON_VER

FROM python:${PYTHON_VER}-slim as base

RUN pip install --upgrade pip \
  && pip install poetry

WORKDIR /local
# Poetry fails install without README.md being copied.
COPY pyproject.toml poetry.lock README.md /local/
COPY schema_enforcer /local/schema_enforcer

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# -----------------------------------------------------------------------------
# Defines stage with ansible installed
# -----------------------------------------------------------------------------
FROM base as with_ansible
ARG ANSIBLE_PACKAGE
ARG ANSIBLE_VER
RUN pip install $ANSIBLE_PACKAGE==$ANSIBLE_VER
