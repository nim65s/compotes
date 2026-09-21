# Docker & deployment

How this project actually ships: a Dockerfile, a docker-compose stack, and
Traefik doing routing and TLS termination in front of it.

## The Dockerfile

```dockerfile
FROM python:3.11
EXPOSE 8000
WORKDIR /app
ENV POETRY_VIRTUALENVS_IN_PROJECT=true PYTHONUNBUFFERED=1 PATH=/root/.local/bin:$PATH

CMD while ! nc -z postgres 5432; do sleep 1; done \
 && poetry run ./manage.py migrate \
 && poetry run ./manage.py collectstatic --no-input \
 && poetry run gunicorn --bind 0.0.0.0 compotes.wsgi
```

Read the `CMD` as a startup sequence for every deploy, in order:

1. **Wait for Postgres.** `nc -z postgres 5432` (netcat, "zero-I/O mode",
   just tests whether a TCP port is open) loops until the `postgres` service
   (see below — Docker Compose's internal DNS resolves the *service name* to
   its container) is actually accepting connections. Without this, the app
   container could start and try to connect before Postgres has finished
   initializing, especially on a cold start of the whole stack.
2. **`manage.py migrate`.** Applies any pending migrations
   ([01-django-concepts.md § Migrations](01-django-concepts.md#migrations))
   automatically on every deploy — so shipping a schema change (like the
   `Event` model) is just "deploy the new code," no
   separate manual migration step to remember.
3. **`manage.py collectstatic`.** Gathers every app's CSS/JS/images into one
   directory (`STATIC_ROOT`, `/srv/compotes/static/` per
   [settings.py:127](../compotes/settings.py#L127)) so they can be served as
   plain files instead of through Django/gunicorn — see the `nginx` service
   below.
4. **`gunicorn`.** The actual production WSGI server (Django's own
   `runserver` is explicitly not meant for production) that serves
   `compotes.wsgi:application`.

The `RUN --mount=type=cache,...` block (installing `gcc`/`libpq-dev`/
`netcat` via `apt`, then `poetry` via `pipx`) uses BuildKit **cache mounts**:
the apt and pip package caches persist *across builds* (not just within one
build's layers), so rebuilding after a small code change doesn't
re-download every dependency from scratch. `poetry` is installed via `pipx`
specifically so *poetry's own* dependencies stay isolated from the
project's virtualenv it's about to create — otherwise you could get version
conflicts between what poetry needs and what compotes needs.

`libpq-dev`/`psycopg2` (in `pyproject.toml`'s `prod` dependency group) is
the PostgreSQL client library — needed to talk to the real `postgres`
service in production, even though local development defaults to SQLite
(`compotes/settings.py:78-84`, controlled by the `DB` env var).

## docker-compose.yml: three services

```yaml
services:
  postgres: { image: postgres:14-alpine, networks: [default] }   # implicit
  app:      { build: ., networks: [web, default] }
  nginx:    { image: nim65s/ndh:nginx, networks: [web] }
```

- **`postgres`** — the database. Notice it's *not* on the `web` network
  (see below) — it should never be reachable from outside the Docker host at
  all, only from `app`, which shares Compose's implicit `default` network
  with it.
- **`app`** — this Django project itself, built from the `Dockerfile` above.
- **`nginx`** — a separate lightweight web server whose *only* job (per its
  Traefik label, `PathPrefix('/static', '/media')`) is serving the files
  `collectstatic` gathered, and user-uploaded media, directly from disk —
  bypassing gunicorn/Django entirely for those paths. This is a standard
  pattern: Django is good at generating dynamic HTML/JSON, but a plain
  static-file server is faster and lighter for files that never change per
  request.

### Networks

```yaml
networks:
  web:
    external: true
```

`web` is an **externally-defined** network (created once, outside this
`docker-compose.yml`, presumably shared by every app on the same host) that
**Traefik** (a reverse proxy, not itself defined in this file — it's
expected to already be running and attached to `web`) uses to discover and
route to containers. Only `app` and `nginx` join `web`; `postgres` never
does — meaning even if Traefik were misconfigured, there's no network path
from the internet-facing proxy straight to the database. `app` *also* joins
Compose's own private `default` network so it can reach `postgres` by
service name (`postgres:5432`, matching `nc -z postgres 5432` in the
Dockerfile and `POSTGRES_HOST` handling in
[settings.py:85-91](../compotes/settings.py#L85-L91)).

### Traefik labels

```yaml
labels:
  traefik.enable: "true"
  traefik.http.routers.compotes-app.rule: "Host(`compotes.${DOMAIN_NAME:-localhost}`)"
```

Traefik watches Docker for containers with these labels and builds its
routing table from them — no separate nginx/Traefik config file to keep in
sync. `Host(...)` matches requests by the `Host` header (i.e. by domain
name); the `nginx` service's rule additionally requires
`PathPrefix('/static', '/media')`, so Traefik sends *only* those two path
prefixes to `nginx` and everything else on the same domain to `app`.
**Traefik itself terminates TLS** — by the time a request reaches the `app`
container, it's plain HTTP. A Django deployment behind a TLS-terminating
proxy like this would normally also set `SECURE_PROXY_SSL_HEADER` (reading
`X-Forwarded-Proto`) plus HSTS/secure-cookie settings so Django itself knows
the original request was secure; this codebase doesn't set those yet — see
`compotes/settings.py`'s `DEBUG`/`CSRF_TRUSTED_ORIGINS` handling for what it
does have.

## Environment variables

Set via a `.env` file (not committed — see `docs/README.md`'s integration
instructions), consumed across `settings.py` and `docker-compose.yml`:

| Variable | Used for |
|---|---|
| `SECRET_KEY` | Django's cryptographic signing key (sessions, CSRF tokens, password reset links) — required whenever `DEBUG=False` |
| `POSTGRES_PASSWORD` | Postgres auth, shared between the `postgres` and `app` containers |
| `DOMAIN_NAME` | Builds the public hostname (`compotes.<DOMAIN_NAME>`) used by both `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` and the Traefik routing rules |
| `DB` | `postgres` in production (else defaults to local SQLite) |
| `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` | SMTP credentials for the weekly balance reminder email |
| `ALLOWED_HOST` | Overrides the auto-derived hostname if needed |
| `CHATONS_ROOT_DIR` | Host-side base path for the bind-mounted volumes (Postgres data, static/media files) |

## The weekly reminder: systemd timer, not cron

```ini
# compotes.timer
[Timer]
OnCalendar=weekly
Persistent=true

# compotes.service
[Service]
ExecStart=/usr/bin/docker exec compotes-app-1 poetry run ./manage.py reminder
```

A **systemd timer** is systemd's built-in alternative to a cron job — the
`.timer` unit defines the schedule (`weekly`; `Persistent=true` means "if the
machine was off when this should have fired, run it once at the next boot
instead of skipping it entirely"), and the matching `.service` unit defines
what actually runs: here, `docker exec` into the already-running `app`
container to invoke `manage.py reminder` — the same management command
tested in `test_reminder`
([compotes/tests.py](../compotes/tests.py)), which emails anyone with a
non-zero balance. `OnFailure=sendmail-wrapper@compotes.service` (in the
`.service` file) means a failed run itself triggers a *notification* email
about the failure — a small but deliberate "don't fail silently" touch.

## Deployment checklist, derived from all of the above

- [ ] `SECRET_KEY` and `POSTGRES_PASSWORD` are set in `.env` and are real
      random values, not placeholders (`docker-compose exec` a Python shell
      and check `settings.SECRET_KEY` if unsure).
- [ ] `DOMAIN_NAME` matches the domain Traefik is actually routing, and DNS
      for it points at this host.
- [ ] The external `web` Docker network already exists and Traefik is
      attached to it before `docker compose up`.
- [ ] After deploying a schema change (like the `Event` model),
      confirm the `app` container's logs show `migrate` actually ran and
      succeeded — it happens automatically, but silently failing would leave
      the app serving against a stale schema.
- [ ] `manage.py check --deploy` has been run against production settings
      and every warning it reports has been consciously accepted or
      addressed (as of this doc, `SECURE_PROXY_SSL_HEADER`/HSTS/secure-cookie
      settings aren't set yet, so expect warnings about those specifically).
