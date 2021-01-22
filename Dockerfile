ARG PYTHON_VER

FROM python:${PYTHON_VER}-slim as base

RUN pip install --upgrade pip \
  && pip install poetry

WORKDIR /local
COPY pyproject.toml /local

ARG ANSIBLE_VER=latest

RUN poetry config virtualenvs.create false \
  && if [ "$ANSIBLE_VER" = "latest" ]; then pip install ansible; else pip install ansible==$ANSIBLE_VER; fi \
  && poetry install --no-interaction --no-ansi

FROM base as without_ansible

RUN pip uninstall -yq ansible ansible-base
