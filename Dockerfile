FROM python:3.9 as poetry

MAINTAINER Harrison Totty <harrisongtotty@gmail.com>

ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=false \
    POETRY_VERSION=1.1.7 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

RUN pip install "poetry==$POETRY_VERSION"


FROM poetry as import

ADD . /project

WORKDIR /project


FROM import as build

RUN poetry install \
    --no-ansi \
    --no-dev \
    --no-interaction \
    --no-root \
    && poetry build \
    --format wheel \
    && pip install dist/*.whl


FROM build as test

RUN poetry install --no-ansi --no-interaction --no-root && \
    mypy --install-types --non-interactive && \
    pytest


FROM build as release
