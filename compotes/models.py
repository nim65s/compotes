"""Compotes models."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.urls import reverse

from ndh.models import Links, TimeStampedModel, NamedModel
from ndh.utils import query_sum


class User(AbstractUser):
    """Placeholder."""

    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        """Meta."""

        ordering = ["username"]

    def update(self):
        """Update the balance."""
        debts = query_sum(self.debt_set, "value", output_field=models.FloatField())
        parts = query_sum(self.part_set, "value", output_field=models.FloatField())
        pools = query_sum(
            self.pool_set.exclude(ratio=0), "value", output_field=models.FloatField()
        )
        shares = query_sum(self.share_set, "value", output_field=models.FloatField())
        self.balance = debts + pools - parts - shares
        self.save()


class Debt(Links, TimeStampedModel):
    """Declare a debt amount."""

    scribe = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    creditor = models.ForeignKey(User, on_delete=models.PROTECT)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    part_value = models.FloatField(default=0)
    description = models.TextField(blank=True)

    def __str__(self):
        """Show PK."""
        return f"debt {self.pk}"

    def get_absolute_url(self):
        """Url to detail self."""
        return reverse("debt_detail", kwargs={"pk": self.pk})

    def get_edit_url(self):
        """Url to edit self."""
        return reverse("debt_update", kwargs={"pk": self.pk})

    def get_parts_url(self):
        """Url to update self parts."""
        return reverse("parts_update", kwargs={"pk": self.pk})

    def update(self):
        """Update part_value, parts, and balances."""
        parts = query_sum(self.part_set, "part", output_field=models.FloatField())
        self.part_value = 0 if parts == 0 else float(self.value) / parts
        self.save()
        for part in self.part_set.all():
            part.update()
        for user in User.objects.filter(Q(part__debt=self) | Q(debt=self)):
            user.update()

    def get_debitors(self):
        """Get number of parts."""
        return self.part_set.count()


class Part(models.Model):
    """Part of a Debt."""

    debt = models.ForeignKey(Debt, on_delete=models.PROTECT)
    debitor = models.ForeignKey(User, on_delete=models.PROTECT)
    part = models.FloatField(default=1)
    value = models.FloatField(default=0)

    class Meta:
        """Meta."""

        unique_together = ["debt", "debitor"]

    def update(self):
        """Update value."""
        self.value = self.part * self.debt.part_value
        self.save()


class Pool(Links, TimeStampedModel, NamedModel):
    """Create a crowd funding."""

    organiser = models.ForeignKey(User, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    ratio = models.FloatField(default=0)

    def get_absolute_url(self):
        """Url to detail self."""
        return reverse("pool_detail", kwargs={"slug": self.slug})

    def get_edit_url(self):
        """Url to edit self."""
        return reverse("pool_update", kwargs={"slug": self.slug})

    def get_share_url(self):
        """Url to edit ones Share."""
        return reverse("share_update", kwargs={"slug": self.slug})

    def update(self):
        """Update ratio, value, shares, and balances."""
        available = query_sum(self.share_set, "maxi", output_field=models.FloatField())
        if available >= self.value:
            self.ratio = float(self.value) / available
            self.save()
            for share in self.share_set.all():
                share.update()
            for user in User.objects.filter(Q(share__pool=self) | Q(pool=self)):
                user.update()


class Share(models.Model):
    """Share of a crowd funding."""

    pool = models.ForeignKey(Pool, on_delete=models.PROTECT)
    participant = models.ForeignKey(User, on_delete=models.PROTECT)
    maxi = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    value = models.FloatField(default=0)

    class Meta:
        """Meta."""

        unique_together = ["pool", "participant"]

    def update(self):
        """Update value."""
        self.value = float(self.maxi) * self.pool.ratio
        self.save()

    def get_absolute_url(self):
        """Return to Pool."""
        return self.pool.get_absolute_url()
