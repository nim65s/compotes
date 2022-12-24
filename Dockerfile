FROM python:3.11

EXPOSE 8000

WORKDIR /app

ENV PYTHONUNBUFFERED=1

CMD while ! nc -z postgres 5432; do sleep 1; done \
 && poetry run ./manage.py migrate \
 && poetry run ./manage.py collectstatic --no-input \
 && poetry run gunicorn \
    --bind 0.0.0.0 \
    compotes.wsgi

RUN --mount=type=cache,sharing=locked,target=/var/cache/apt \
    --mount=type=cache,sharing=locked,target=/var/lib/apt \
    --mount=type=cache,sharing=locked,target=/root/.cache \
    apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get install -qqy --no-install-recommends \
    gcc \
    libexpat1 \
    libpq-dev \
    netcat \
 && python -m pip install -U pip \
 && python -m pip install -U pipx \
 && python -m pipx install poetry

ENV PATH=/root/.local/bin:$PATH
ADD pyproject.toml poetry.lock ./
RUN --mount=type=cache,sharing=locked,target=/root/.cache \
    python -m venv .venv \
 && poetry install --no-dev --no-root --no-interaction --no-ansi

ADD . .
