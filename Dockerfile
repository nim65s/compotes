FROM python:3.10

EXPOSE 8000

WORKDIR /app

ENV PYTHONUNBUFFERED=1

CMD while ! nc -z postgres 5432; do sleep 1; done \
 && ./manage.py migrate \
 && ./manage.py collectstatic --no-input \
 && gunicorn \
    --bind 0.0.0.0 \
    compotes.wsgi

RUN --mount=type=cache,sharing=locked,target=/var/cache/apt \
    --mount=type=cache,sharing=locked,target=/var/lib/apt \
    --mount=type=cache,sharing=locked,target=/root/.cache \
    apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get install -qqy \
    gcc \
    libexpat1 \
    libpq-dev \
    netcat \
 && python -m pip install -U pip \
 && python -m pip install \
    gunicorn \
    poetry \
    psycopg2 \
 && apt-get autoremove -qqy gcc

ADD pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false --local \
 && poetry install --no-dev --no-root --no-interaction --no-ansi

ADD . .
