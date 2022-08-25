"""Compotes models."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ndh.models import Links, TimeStampedModel, NamedModel
from ndh.utils import query_sum


class User(AbstractUser):
    """Placeholder."""

    balance = models.DecimalField(
        _("Balance"), max_digits=8, decimal_places=2, default=0
    )

    class Meta:
        """Meta."""

        ordering = ["username"]
        verbose_name = _("User")

    def save(self, *args, **kwargs):
        """Update the balance."""
        if self.pk:
            debts = query_sum(
                self.debt_set.exclude(part_value=0),
                "value",
                output_field=models.FloatField(),
            )
            parts = query_sum(self.part_set, "value", output_field=models.FloatField())
            pools = query_sum(
                self.pool_set.exclude(ratio=0),
                "value",
                output_field=models.FloatField(),
            )
            shares = query_sum(
                self.share_set, "value", output_field=models.FloatField()
            )
            self.balance = debts + pools - parts - shares
        super().save(*args, **kwargs)


class Debt(Links, TimeStampedModel):
    """Declare a debt amount."""

    scribe = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="+", verbose_name=_("Scribe")
    )
    creditor = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name=_("Creditor")
    )
    value = models.DecimalField(_("Value"), max_digits=8, decimal_places=2)
    part_value = models.FloatField(_("Part value"), default=0)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        """Meta."""

        verbose_name = _("Debt")

    def __str__(self) -> str:
        """Show PK."""
        return f"debt {self.pk}"

    def get_absolute_url(self) -> str:
        """Url to detail self."""
        return reverse("debt_detail", kwargs={"pk": self.pk})

    def get_edit_url(self) -> str:
        """Url to edit self."""
        return reverse("debt_update", kwargs={"pk": self.pk})

    def get_parts_url(self) -> str:
        """Url to update self parts."""
        return reverse("parts_update", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        """Update part_value, parts, and balances."""
        if self.pk:
            parts = query_sum(self.part_set, "part", output_field=models.FloatField())
            self.part_value = 0 if parts == 0 else float(self.value) / parts
        super().save(*args, **kwargs)
        for part in self.part_set.all():
            part.save(allow_rec=False)
        for user in User.objects.filter(Q(part__debt=self) | Q(debt=self)):
            user.save()

    def get_debitors(self) -> int:
        """Get number of debitors."""
        return User.objects.filter(part__debt=self).distinct().count()

    def get_parts(self) -> int:
        """Get number of parts."""
        return self.part_set.count()


class Part(models.Model):
    """Part of a Debt."""

    debt = models.ForeignKey(Debt, on_delete=models.PROTECT, verbose_name=_("Debt"))
    debitor = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name=_("Debitor")
    )
    part = models.FloatField(_("Part"), default=1)
    value = models.FloatField(_("Value"), default=0)
    description = models.CharField(_("Description"), max_length=1000, blank=True)

    class Meta:
        """Meta."""

        verbose_name = _("Part")

    def save(self, *args, allow_rec=True, **kwargs):
        """Update value."""
        self.value = self.part * self.debt.part_value
        super().save(*args, **kwargs)
        if allow_rec:
            self.debt.save()


class Pool(Links, TimeStampedModel, NamedModel):
    """Create a crowd funding."""

    organiser = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name=_("Organiser")
    )
    description = models.TextField(_("Description"), blank=True)
    value = models.DecimalField(_("Value"), max_digits=8, decimal_places=2)
    ratio = models.FloatField(_("Ratio"), default=0)

    class Meta:
        """Meta."""

        verbose_name = _("Pool")

    def get_absolute_url(self) -> str:
        """Url to detail self."""
        return reverse("pool_detail", kwargs={"slug": self.slug})

    def get_edit_url(self) -> str:
        """Url to edit self."""
        return reverse("pool_update", kwargs={"slug": self.slug})

    def get_share_url(self) -> str:
        """Url to edit ones Share."""
        return reverse("share_update", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        """Update ratio, value, shares, and balances."""
        if self.pk:
            available = query_sum(
                self.share_set, "maxi", output_field=models.FloatField()
            )
            self.ratio = float(self.value) / available if available >= self.value else 0
        super().save(*args, **kwargs)
        for share in self.share_set.all():
            share.save(allow_rec=False)
        for user in User.objects.filter(Q(share__pool=self) | Q(pool=self)):
            user.save()


class Share(models.Model):
    """Share of a crowd funding."""

    pool = models.ForeignKey(Pool, on_delete=models.PROTECT, verbose_name=_("Pool"))
    participant = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name=_("Participant")
    )
    maxi = models.DecimalField(_("Maxi"), max_digits=8, decimal_places=2, default=0)
    value = models.FloatField(_("Value"), default=0)

    class Meta:
        """Meta."""

        unique_together = ["pool", "participant"]
        verbose_name = _("Share")

    def save(self, *args, allow_rec=True, **kwargs):
        """Update value, and trigger pool update."""
        self.value = float(self.maxi) * self.pool.ratio
        super().save(*args, **kwargs)
        if allow_rec:
            self.pool.save()

    def get_absolute_url(self) -> str:
        """Return to Pool."""
        return self.pool.get_absolute_url()
