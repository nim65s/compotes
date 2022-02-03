# Compotes

[![Tests](https://github.com/nim65s/compotes/actions/workflows/test.yml/badge.svg)](https://github.com/nim65s/compotes/actions/workflows/test.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/nim65s/compotes/master.svg)](https://results.pre-commit.ci/latest/github/nim65s/compotes/master)
[![codecov](https://codecov.io/gh/nim65s/compotes/branch/master/graph/badge.svg?token=75XO2X5QW0)](https://codecov.io/gh/nim65s/compotes)
[![Maintainability](https://api.codeclimate.com/v1/badges/a0783da8c0461fe95eaf/maintainability)](https://codeclimate.com/github/nim65s/compotes/maintainability)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Track debts & pools

## Dev

```bash
poetry install
poetry run ./manage.py migrate
poetry run ./manage.py createsuperuser
poetry run ./manage.py runserver
```

## Integration

```bash
echo POSTGRES_PASSWORD=$(openssl rand -base64 32) >> .env
echo SECRET_KEY=$(openssl rand -base64 32) >> .env
docker compose up -d --build
docker compose exec app ./manage.py createsuperuser
```

## Prod

Same, but with a real `DOMAIN_NAME` and with `DEBUG=False`. And don't forget https.
