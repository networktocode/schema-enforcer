ARG PYTHON_VER

FROM python:${PYTHON_VER}-slim as base

RUN pip install --upgrade pip \
  && pip install poetry

WORKDIR /local
COPY pyproject.toml /local

ARG ANSIBLE_VER="ignore"

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi \
  # If ANSIBLE_VER is set (not default), uninstall the ansible version poetry installed and install the declared ansible version.
  && if not [ "$ANSIBLE_VER" = "ignore" ]; then pip uninstall -yq ansible ansible-base && pip install ansible==$ANSIBLE_VER; fi

FROM base as without_ansible

RUN pip uninstall -yq ansible ansible-base
