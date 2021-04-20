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
# Defines stage with ansible-base installed
# -----------------------------------------------------------------------------
FROM base as with_ansible_base
ARG ANSIBLE_BASE_VER
RUN pip install ansible-base==$ANSIBLE_BASE_VER

# -----------------------------------------------------------------------------
# Defines stage with ansible installed
# -----------------------------------------------------------------------------
FROM base as with_ansible
ARG ANSIBLE_VER
RUN pip install ansible==$ANSIBLE_VER
