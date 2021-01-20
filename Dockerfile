ARG PYTHON_VER

FROM python:${PYTHON_VER}-slim as base

RUN pip install --upgrade pip \
  && pip install poetry

WORKDIR /local
COPY pyproject.toml /local

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

FROM base as with_ansible

ARG ANSIBLE_VER=latest

RUN if [ "$ANSIBLE_VER" = "latest" ]; then pip install ansible; else pip install ansible==$ANSIBLE_VER; fi
