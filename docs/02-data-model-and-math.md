# The data model and the money math

This is the part of the codebase most worth scrutinizing line-by-line, since
a bug here means someone's balance is silently wrong. Every number below is
copy-pasted from an actual passing test, so you can reproduce all of it in
`manage.py shell`.

## The four models and how they relate

```
User ──creditor of──> Debt <──debt of── Part ──debitor is── User
User ──organiser of──> Pool <──pool of── Share ──participant is── User
```

- A **Debt** is "X paid value €, split into parts among some people."
- A **Part** is one person's share of a Debt, expressed as a *ratio*
  (`part`), not a fixed amount — e.g. two people splitting a bill 50/50 both
  get `part=1`; someone paying double gets `part=2`.
- A **Pool** is a crowdfunding goal: "we need value € total."
- A **Share** is one person's pledge (`maxi`, the *most* they're willing to
  contribute) toward a Pool.
- Every `User` has a single stored `balance` field: positive means "the group
  owes you money," negative means "you owe the group."

## The `save()`-cascade pattern

This codebase does **not** use Django signals (`post_save`, etc.) to keep
derived numbers in sync. Instead, every model's own `.save()` method
recomputes what it owns, then walks its own relations and calls `.save()` on
each affected row, which in turn does the same thing one level further out.
For example, `Debt.save()`:

```python
def save(self, *args, **kwargs):
    if self.pk:
        parts = query_sum(self.part_set, "part", output_field=models.FloatField())
        self.part_value = 0 if parts == 0 else float(self.value) / parts
    super().save(*args, **kwargs)
    for part in self.part_set.all():
        part.save(allow_recursion=False)
    for user in User.objects.filter(Q(part__debt=self) | Q(debt=self)):
        user.save()
```
([compotes/models.py:231-240](../compotes/models.py#L231-L240))

Saving a `Debt` recomputes `part_value`, re-saves every `Part` of it (which
recomputes each Part's `value`), then re-saves every `User` involved
(creditor + every debitor), which recomputes their `balance`. `Part.save()`
does the mirror image: it recomputes its own `value`, then calls
`self.debt.save()` — so *either* end of the relationship changing propagates
correctly. The `allow_recursion` flag exists purely to stop this from
becoming an infinite Debt→Part→Debt→Part loop: when `Debt.save()` re-saves
its Parts, it passes `allow_recursion=False` so those Part saves don't call
back into `Debt.save()` again (which just ran anyway).

**Why this matters for review:** this pattern is simple to read top-to-bottom
— no hidden signal handlers to go hunting for — but it means:
- Every write does more database work than a batched/async approach would
  (creating one Debt with 4 Parts triggers 1 Debt save + 4 Part saves + up to
  5 User saves = 10 writes). Fine at friend-group scale; would need
  rethinking if this app ever handled thousands of Parts per Debt.
- **Bulk operations bypass this entirely.** `Debt.objects.filter(...).update(...)`
  or `Part.objects.bulk_create(...)` do not call `.save()` and therefore
  silently skip the recompute. Nothing in this codebase currently does bulk
  writes on these models, but it's the sharp edge to remember if you extend
  it — always use `.save()` (or explicitly re-trigger the cascade) for these
  models, never `.update()`/`bulk_create()`.

## Debt & Part math, worked example

From `test_models_debt` in [compotes/tests.py](../compotes/tests.py):

```python
creditor = a  # first of 4 users: a, b, c, d
debt = Debt.objects.create(creditor=a, value=100.03, name="debt 1")
for user in (a, b, c, d):
    Part.objects.create(debt=debt, debitor=user, part=25)
```

Everyone gets `part=25` — an equal split expressed as equal ratios, four
people. `Debt.save()` computes:

```
part_value = value / total_parts = 100.03 / (25+25+25+25) = 100.03 / 100 = 1.0003
```

Then each `Part.save()` computes `value = part * debt.part_value`:

```
each Part.value = 25 * 1.0003 = 25.0075
```

Finally each `User.save()` computes `balance = pool_sum + debts − parts`
([compotes/models.py:54-64](../compotes/models.py#L54-L64)). For user **a**,
who is *both* the creditor and one of the four debitors:

```
a.balance = 0 (no pool activity) + 100.03 (creditor of the whole debt) − 25.0075 (a's own part)
          = 75.0225 → stored as Decimal, rounds to 75.02
```

For user **d**, who only has a Part (not the creditor):

```
d.balance = 0 + 0 − 25.0075 = −25.0075 → rounds to −25.01
```

Sign convention: being a **creditor** adds the full debt value to your
balance (people owe you); holding a **Part** subtracts your share (you owe
that much). The two only cancel out when you're the creditor *and* you paid
your own share as one of the debitors — which is exactly what happens here
for `a`.

## Pool & Share math, worked example

A `Pool` is different from a `Debt` in one important way: nobody is charged
until enough people have pledged to cover the goal. From `test_models_pool`:

```python
pool = Pool.objects.create(name="smth", organiser=a, description="smth", value=100)
for user in (a, b, c, d):
    Share.objects.create(pool=pool, participant=user, maxi=30)
```

`Pool.save()` ([compotes/models.py:320-329](../compotes/models.py#L320-L329)):

```python
available = float(self.sum_shares())          # sum of everyone's `maxi`
self.ratio = float(self.value) / available if available >= self.value else 0
```

Here `sum_shares() = 4 × 30 = 120`, which is `>= value (100)`, so:

```
ratio = 100 / 120 = 0.8333...
```

**If pledges hadn't reached the goal, `ratio` would stay `0` and nobody would
be charged anything** — `Share.save()` computes `value = maxi × ratio`, so a
`ratio` of `0` means every `Share.value` is `0` too. This protects
participants from being charged toward a goal that never got funded. Once
funded, each participant only pays their pledge (`maxi`) scaled down by how
much *over*-funded the pool ended up (`ratio ≤ 1` whenever `available ≥ value`,
i.e. everyone pays less than they offered, proportionally, if the pool was
over-subscribed):

```
each Share.value = 30 × 0.8333... = 25
```

Balances: the organiser **a**'s `get_pool_sum()`
([compotes/models.py:100-108](../compotes/models.py#L100-L108)) is *pools
they organise* minus *shares they've pledged*:

```
a.balance = 100 (the pool's value, since it's now funded/ratio≠0) − 25 (a's own share) = 75
```

Everyone else, who only has a Share and organises nothing:

```
b.balance = c.balance = d.balance = 0 − 25 = −25
```

`75 + (−25×3) = 0` — money in the system always nets to zero, which is also
exactly what `test_models_pool` and `test_rand` (a randomized fuzz test)
assert.

## A note on Decimal vs float

Money fields in this codebase are a mix of two Python number types:

- `DecimalField` (`User.balance`, `Debt.value`, `Pool.value`, `Share.maxi`) —
  backed by Python's `decimal.Decimal`, which represents numbers exactly in
  base 10 (no binary rounding surprises). This is the type you want for a
  number that gets *displayed and stored as the ground truth*.
- `FloatField` (`Debt.part_value`, `Part.part`/`value`, `Pool.ratio`,
  `Share.value`) — backed by ordinary binary floating point, used for
  intermediate *ratios and per-unit values* — `part_value = value / total_parts`
  can be an irrational-looking repeating fraction (`100.03 / 3 = 33.343333...`),
  which `Decimal` handles awkwardly without an explicit rounding/precision
  policy, so the original author used `float` there instead.

The stored `balance` field is still `Decimal`, and Django's ORM converts the
final `float` result back to `Decimal` on save — so what you see in
`User.balance` is always properly rounded to 2 places. The risk this
trade-off carries is float's imprecision *compounding* across many
sequential operations before that final rounding — negligible at the amounts
and part-counts a friend group deals with (the worked examples above show
errors on the order of a fraction of a cent), but worth knowing about if this
app ever needed to handle very large sums or very finely split parts.

Next: [03-docker-deployment.md](03-docker-deployment.md) covers how this
gets deployed.
