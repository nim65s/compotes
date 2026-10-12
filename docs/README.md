# Compotes implementation docs

A from-scratch walkthrough of this codebase's Django patterns and the
balance math behind it, written for someone who knows how to code but
hasn't necessarily touched Django — every Django concept is explained the
first time it's used, grounded in this repo's actual lines.

## Reading order

1. [01-django-concepts.md](01-django-concepts.md) — Django/Python vocabulary used everywhere else: models, migrations, QuerySets, class-based views, mixins, URL routing. Skip if you already know Django.
2. [02-data-model-and-math.md](02-data-model-and-math.md) — the actual money math: how a Debt splits into Parts, how a Pool's ratio works. This is the part most worth scrutinizing.
3. [03-docker-deployment.md](03-docker-deployment.md) — the Dockerfile, docker-compose, Traefik, and the systemd timer for the weekly reminder email.

## Trust model & known trade-offs

Judgment calls made explicit, not bugs:

| Trade-off | Why | Where |
|---|---|---|
| Money fields mix `Decimal` (stored balances) and `float` (intermediate math like `part_value`, `ratio`) | Inherited from the original code; fine at friend-group amounts and part-counts, but it's not the bulletproof choice a bank would make | [02-data-model-and-math.md § A note on Decimal vs float](02-data-model-and-math.md#a-note-on-decimal-vs-float) |
| Balances recompute by walking and re-saving every affected row on every write, not via async tasks or DB triggers | Simple to read top-to-bottom, at the cost of doing more DB writes than strictly necessary per request | [02-data-model-and-math.md § The save()-cascade pattern](02-data-model-and-math.md#the-save-cascade-pattern) |
| `on_delete=PROTECT` everywhere | You can never delete a User/Debt/Pool/Event that's still referenced elsewhere — deliberately prevents silent data loss, at the cost of needing manual cleanup for real deletions | [01-django-concepts.md § Models](01-django-concepts.md#models) |

## How to verify any of this yourself

```bash
# from the compotes/ directory
poetry install --with dev
poetry run python manage.py migrate
poetry run python manage.py test compotes actions  # 16 tests should pass
poetry run python manage.py check --deploy  # security checklist
```

Every numeric example in [02-data-model-and-math.md](02-data-model-and-math.md)
matches an assertion in `compotes/tests.py` — you can open `manage.py shell`
and re-run the same `Debt.objects.create(...)` calls to see the numbers
land yourself, instead of trusting the doc.
