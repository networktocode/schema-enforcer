ARG PYTHON

FROM python:${PYTHON}-slim

RUN pip install --upgrade pip \
  && pip install poetry

WORKDIR /local
COPY pyproject.toml /local

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi
