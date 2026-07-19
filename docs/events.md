# The events feature: isolating a sub-ledger

An **Event** optionally tags a Debt as belonging to an isolated sub-ledger,
e.g. a holiday trip — its Debts stay off everyone's global balance until
the Event is explicitly closed. Every number below is copy-pasted from an
actual passing test, so you can reproduce all of it in `manage.py shell`.

Recap of the two models this builds on: a **Debt** is "X paid value €, split
into parts among some people," and a **Part** is one person's share of it.
Every `User` has a single stored `balance` field: positive means "the group
owes you money."

The trick is entirely in two `User` methods:

```python
def get_debts(self, event=None):
    debts = self.debt_set.exclude(part_value=0)
    if event is not None:
        return debts.filter(event=event)
    return debts.filter(Q(event__isnull=True) | Q(event__closed_at__isnull=False))
```
([compotes/models.py:66-76](../compotes/models.py#L66-L76), `get_parts` on
[lines 78-84](../compotes/models.py#L78-L84) mirrors this exactly for the
debitor side.)

Read the filter as a small truth table for "does this Debt count toward the
**global** balance" (i.e. when `event=None`, the default used by
`User.save()`):

| Debt.event | Event.closed_at | Counts toward global balance? |
|---|---|---|
| `NULL` (no event) | — | Yes — always did, this is the pre-Event behavior |
| set | `NULL` (open) | **No** — isolated in its own Event |
| set | set (closed) | Yes — folded back in |

`get_event_balance(event)` ([compotes/models.py:86-98](../compotes/models.py#L86-L98))
calls the same two methods *with* an event, computing that Event's own
isolated balance the same way `User.save()` computes the global one.

**Why closing needs no data migration.** `Event.close()` and `.reopen()`
([compotes/models.py:182-190](../compotes/models.py#L182-L190)) do nothing but
flip `closed_at` and call `.save()`, which (via `Event.save()`, [lines
170-174](../compotes/models.py#L170-L174)) re-saves every participant. No
`Debt` or `Part` row is ever touched — the *same* rows simply start being
read differently by the `get_debts`/`get_parts` filter above. This is also
why reopening is a free, lossless undo: nothing was destroyed, only a
timestamp was set and then cleared.

Worked example, from `EventTests.test_event_close_and_reopen`
([compotes/tests.py](../compotes/tests.py)):

```python
event = Event.objects.create(name="trip", organiser=a)
debt = Debt.objects.create(creditor=a, value=100, name="hotel", event=event)
Part.objects.create(debt=debt, debitor=b, part=1)
```

While `event.closed_at` is `None`:

```
a.balance == 0          # the debt is isolated, doesn't touch the global figure
b.balance == 0
a.get_event_balance(event) == 100     # but it IS visible inside the event
b.get_event_balance(event) == -100
```

After `event.close()`:

```
a.balance == 100        # folded straight into the global balance
b.balance == -100
```

After `event.reopen()`, both go back to `0` — isolated again, no data lost.

The **close confirmation** (in [compotes/views.py](../compotes/views.py)'s
`EventCloseView`) computes each participant's `get_event_balance` *before*
closing; if anyone is non-zero, it refuses with a flash message unless the
caller explicitly confirms (a checked checkbox) — matching the "ask before
folding unsettled debts into the global pool" behavior agreed on with the
user.
