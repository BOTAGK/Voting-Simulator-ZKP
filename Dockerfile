FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

ARG SNARKJS_VERSION=0.7.5

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g snarkjs@${SNARKJS_VERSION} \
    && pip install --no-cache-dir poetry

COPY package.json package-lock.json ./
RUN npm ci

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main

COPY app ./app
COPY circuits ./circuits
COPY scripts ./scripts

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
