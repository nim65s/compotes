# Django concepts, taught from this codebase

Django is a web framework built around three layers, historically called
**Model-View-Template (MTV)** — Django's own twist on the more common
Model-View-Controller name:

- **Model** — Python classes that describe your database tables (`compotes/models.py`).
- **View** — Python functions/classes that take a web request and return a response (`compotes/views.py`).
- **Template** — HTML files with a small templating language, rendered by a View (`compotes/templates/`).

A request comes in, Django's URL router (`urls.py`) picks a View based on the
path, the View talks to Models to read/write the database, and (for HTML
pages) renders a Template with the result.

This project has two Django "apps" (self-contained Python packages plugged
into one project): `compotes` (the core domain — users, debts, pools) and
`actions` (an audit log). Both are listed in `INSTALLED_APPS` in
[compotes/settings.py:27-42](../compotes/settings.py#L27-L42) — that list
is how Django knows which apps' models/templates/admin registrations to
load.

## Models

A Model is a Python class where each class attribute is a database column.
Take `Debt` ([compotes/models.py:193-212](../compotes/models.py#L193-L212)):

```python
class Debt(Links, TimeStampedModel):
    name = models.CharField(_("Name"), max_length=200)
    date = models.DateTimeField(_("Date"), default=timezone.now)
    creditor = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_("Creditor"))
    event = models.ForeignKey(Event, on_delete=models.PROTECT, blank=True, null=True, verbose_name=_("Event"))
    value = models.DecimalField(_("Value"), max_digits=8, decimal_places=2)
    part_value = models.FloatField(_("Part value"), default=0)
    description = models.TextField(_("Description"), blank=True)
```

- `CharField`/`TextField` — short vs. long text. `DateTimeField` — a timestamp.
  `DecimalField`/`FloatField` — two different ways to store numbers; see
  [02-data-model-and-math.md](02-data-model-and-math.md#a-note-on-decimal-vs-float)
  for why both are used here and what the trade-off is.
- `ForeignKey` — a reference to another table's row (like a SQL foreign key).
  `creditor = ForeignKey(User, ...)` means every `Debt` row has a `creditor_id`
  column pointing at a `User` row.
- `blank=True, null=True` — `null=True` allows `NULL` in the actual database
  column; `blank=True` allows the field to be left empty in forms/serializers.
  You almost always want both together for an optional field, which is why
  `Debt.event` has both — a Debt doesn't have to belong to an Event.
- `on_delete=models.PROTECT` — what happens to this row if the thing it
  points to gets deleted. `PROTECT` means "refuse the delete, raise an error."
  Every foreign key in this codebase uses `PROTECT` (never `CASCADE`, which
  would silently delete dependent rows too). That's a deliberate safety choice:
  you cannot delete a `User` who still has debts, or a `Pool` that still has
  shares, without Django stopping you — it forces an explicit decision instead
  of a silent cascade of deletions.
- `_(...)` is `gettext_lazy`, Django's translation marker — it doesn't affect
  logic, it just makes the string translatable.
- `Links`, `TimeStampedModel` (and `NamedModel`, used by `Event`/`Pool`) are
  **mixins** from a third-party package (`ndh`) that this project depends on —
  see [Mixins & MRO](#mixins-and-method-resolution-order-mro) below.
  `TimeStampedModel` adds `created`/`updated` auto-managed timestamp columns;
  `NamedModel` adds a `name` field plus an auto-generated URL `slug`;
  `Links` adds helper methods like `get_link()` used in templates.

### Migrations

Every time a Model's fields change, Django needs to generate a matching SQL
schema change. `python manage.py makemigrations` diffs your Models against
the last known schema and writes a migration file describing the change (as
Python, not raw SQL, so it's Django-version portable). `python manage.py
migrate` actually applies pending migration files to the database.

[compotes/migrations/0017_event_debt_event.py](../compotes/migrations/0017_event_debt_event.py)
is the migration this project generated for the `Event` feature — it has two
operations: `CreateModel("Event", ...)` and `AddField("debt", "event", ...)`.
Because `event` is `null=True`, adding it to the existing `Debt` table needs no
data backfill: every existing row just gets `NULL` in the new column, which is
exactly the "not in any Event" state the balance math already expects.

Migrations are checked into git and applied in order — never hand-edit an
already-applied migration; instead generate a new one. You can sanity-check
that no model change was left un-migrated with:

```bash
python manage.py makemigrations --check --dry-run
```

## QuerySets

Every `Model.objects` (e.g. `User.objects`, `Debt.objects`) is a **Manager**;
calling `.all()`, `.filter()`, etc. on it returns a **QuerySet** — a lazy,
chainable representation of a SQL query that only actually hits the database
when you iterate it, print it, or call something like `.count()`.

```python
self.debt_set.exclude(part_value=0)
```
(from [compotes/models.py:73](../compotes/models.py#L73)) — `debt_set` is the
*reverse* side of the `Debt.creditor` foreign key: Django automatically gives
every `User` a `.debt_set` manager listing all `Debt`s where that user is the
creditor. `.exclude(part_value=0)` is `.filter()`'s opposite — "give me every
row that does *not* match."

**`Q` objects** let you build `OR`/complex conditions, since `.filter(a=1, b=2)`
is always `AND`:

```python
User.objects.filter(Q(debt__event=self) | Q(part__debt__event=self)).distinct()
```
(from [compotes/models.py:178-180](../compotes/models.py#L178-L180)) — reads as
"every User who is either the creditor of a Debt in this Event, or the
debitor (via a Part) of a Debt in this Event." `debt__event` is a
**double-underscore lookup**: it walks the reverse relation from `User` to
`Debt` and then across `Debt.event` to filter on the `Event`'s own fields —
you can chain these arbitrarily deep across relations. `.distinct()` dedupes,
since a user could otherwise appear once as creditor and once as debitor.

This project also uses a small helper, `query_sum` (from the `ndh` package)
instead of Django's own `.aggregate(Sum(...))`, mainly to get a plain `0`
back instead of `None` when the QuerySet is empty — same idea, less
boilerplate at each call site.

## Class-based views

Rather than writing one function per URL, this project uses Django's
**class-based views** (`CBVs`): pre-built classes for common patterns —
`ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView` — that you
customize by setting class attributes or overriding a handful of methods.

```python
class DebtDetailView(LoginRequiredMixin, DetailView):
    model = Debt

    def get_context_data(self, **kwargs):
        actions = Action.objects.filter(...)
        return super().get_context_data(actions=actions, form=PartForm(), **kwargs)
```
(from [compotes/views.py](../compotes/views.py)) — `model = Debt` is enough
for `DetailView` to know how to fetch the right row (from the URL's `<pk>`)
and which template to render (`compotes/debt_detail.html`, by convention:
`<app>/<model>_detail.html`). `get_context_data` is the hook for adding
extra variables the template needs beyond the model instance itself; always
call `super()` and pass its return value's contents through, or you'll
silently lose the variables Django itself would have added.

### Mixins and Method Resolution Order (MRO)

Python supports multiple inheritance, and Django CBVs lean on it heavily via
**mixins** — small classes that each add one piece of behavior, combined by
listing several base classes:

```python
class EventCreateView(LoginRequiredMixin, NDHFormMixin, ActionCreateMixin, CreateView):
```

Each of these contributes something: `LoginRequiredMixin` redirects
anonymous users to the login page before anything else runs;
`NDHFormMixin` sets a default form template/title; `ActionCreateMixin`
(from the `actions` app, [actions/views.py](../actions/views.py)) logs an
audit-trail `Action` row after a successful save; `CreateView` does the
actual "render a form, validate it, save it" work.

**Order matters.** When you call `.form_valid()` on an instance of
`EventCreateView`, Python looks for `form_valid` on each class left-to-right —
this is the MRO. `ActionCreateMixin.form_valid` calls `super().form_valid()`
internally, which (because of the order above) reaches `CreateView.form_valid`
next, which actually persists the object and redirects. If you reordered
these base classes, that chain could break — e.g. if `CreateView` came before
`ActionCreateMixin`, `ActionCreateMixin.form_valid` would never run, since
Python would resolve `form_valid` on `CreateView` first and stop there.

## URL routing

[compotes/urls.py](../compotes/urls.py) maps URL patterns to views:

```python
path("event/<slug:slug>", views.EventDetailView.as_view(), name="event_detail"),
```

`<slug:slug>` is a **path converter**: it matches a URL segment made of
letters/numbers/hyphens and passes it to the view as a keyword argument
named `slug`. `<int:pk>` (used for `Debt`, e.g. `/debt/1`) does the same for
integers. Which one a model uses depends on whether it has a slug field
(`Event`/`Pool` do, via the `NamedModel` mixin) or not (`Debt` doesn't, so it
falls back to the numeric primary key).

`name="event_detail"` registers a **URL name** you can reverse-look-up from
anywhere — in Python via `reverse("event_detail", kwargs={"slug": "trip"})`,
or in a template via `{% url 'event_detail' slug=event.slug %}` — instead of
hardcoding path strings, which would break the moment the URL pattern
changed.

If a second app defined its own `urls.py` and got `include()`d with
`app_name = "something"`, that name would **namespace** every URL name
inside it, so `reverse("something:token")` and a bare `reverse("token")`
elsewhere can't collide — worth knowing even though this project's own
`urls.py` doesn't need it today.

## Templates

```html
{% extends "base.html" %}
{% load django_bootstrap5 i18n %}

{% block content %}
<h1>{% translate "Event" %}: {{ event }}</h1>
{% include "compotes/_event_detail.html" %}
{% endblock %}
```

- `{% extends %}` — this template fills in a `{% block %}` defined in a parent
  template (`base.html`), which owns the page's `<html>`/nav/footer.
- `{% load %}` — imports extra template tags from an app (here,
  `django-bootstrap5`'s form-rendering helpers, and Django's own
  `i18n`/`{% translate %}`).
- `{{ event }}` — prints a Python value, calling `str(event)` (or, for a
  model without `__str__` overridden, Django's default representation).
  Auto-**escaped** by default (so a Debt name containing `<script>` renders
  as harmless text, not executable HTML) — the one deliberate exception in
  this codebase is `Links.get_link()`, which returns pre-built, trusted HTML
  wrapped in `mark_safe()` and is used specifically to render a clickable
  link (e.g. `{{ debt.event.get_link }}` in
  [_debt_detail.html](../compotes/templates/compotes/_debt_detail.html)).
- `{% include %}` — splices another template in, useful for partials reused
  across pages (`_event_detail.html`/`_pool_detail.html`/`_debt_detail.html`
  are all such partials, conventionally prefixed with `_`).

## Admin

```python
for model in (models.Debt, models.Event, models.Part, models.Pool, models.Share):
    admin.site.register(model)
```
(from [compotes/admin.py](../compotes/admin.py)) — one line per model gives
you a full CRUD web UI at `/admin/` for free, meant for the site operator
(superuser), not regular users. `User` gets a more customized registration
just above it, adding the computed `balance` field to the list display.

With this vocabulary in hand, [02-data-model-and-math.md](02-data-model-and-math.md)
walks through the actual financial logic.
