"""Compotes models."""

from smtplib import SMTPException

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.mail import mail_admins
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField  # type: ignore
from dmdm import send_mail
from ndh.models import Links, NamedModel, TimeStampedModel
from ndh.utils import query_sum


class User(Links, AbstractUser):
    """Placeholder."""

    slug = AutoSlugField(populate_from="username", unique=True)
    balance = models.DecimalField(
        _("Balance"), max_digits=8, decimal_places=2, default=0
    )
    respo = models.ForeignKey("self", on_delete=models.PROTECT, blank=True, null=True)

    class Meta:
        """Meta."""

        ordering = ["username"]
        verbose_name = _("User")

    def get_absolute_url(self) -> str:
        """Get url to this User."""
        return reverse("user_detail", kwargs={"slug": self.slug})

    def __repr__(self):
        """Display users by their name and/or username."""
        name = f"{self.first_name} {self.last_name}".strip()
        if (
            self.username.lower() not in self.first_name.lower()
            and self.username.lower() not in self.last_name.lower()
        ):
            if name:
                return f"{name} ({self.username})"
            return self.username
        return name

    def save(self, *args, **kwargs):
        """Update the balance."""
        if self.pk:
            debts = query_sum(
                self.get_debts(),
                "value",
                output_field=models.FloatField(),
            )
            parts = query_sum(self.part_set, "value", output_field=models.FloatField())
            self.balance = self.get_pool_sum() + debts - parts
        super().save(*args, **kwargs)

    def get_debts(self):
        """Get debts excluding those without value."""
        return self.debt_set.exclude(part_value=0)

    def get_pool_sum(self):
        """Get sum of Pool participations."""
        pools = query_sum(
            self.pool_set.exclude(ratio=0),
            "value",
            output_field=models.FloatField(),
        )
        shares = query_sum(self.share_set, "value", output_field=models.FloatField())
        return pools - shares

    def send_mail(self, subject, message):
        """Send a mail to this user."""
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                reply_to=[settings.ADMINS[0][1]],
            )
        except SMTPException:  # pragma: no cover
            mail_admins(
                f"SMTP Exception for {self} <{self.email}>", f"{subject=}\n{message=}"
            )

    def reminder(self):
        """Remind users of their balance."""
        if self.balance == 0:
            return
        self.send_mail(
            "Balance Reminder",
            f"Hi {self},\n\n"
            f"This is a weekly reminder: your balance is {self.balance:.2f} €",
        )


class Debt(Links, TimeStampedModel):
    """Declare a debt amount."""

    name = models.CharField(_("Name"), max_length=200)
    date = models.DateTimeField(_("Date"), default=timezone.now)
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
        return f"{self.name}"

    def get_absolute_url(self) -> str:
        """Url to detail self."""
        return reverse("debt_detail", kwargs={"pk": self.pk})

    def get_edit_url(self) -> str:
        """Url to edit self."""
        return reverse("debt_update", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        """Update part_value, parts, and balances."""
        if self.pk:
            parts = query_sum(self.part_set, "part", output_field=models.FloatField())
            self.part_value = 0 if parts == 0 else float(self.value) / parts
        super().save(*args, **kwargs)
        for part in self.part_set.all():
            part.save(allow_recursion=False)
        for user in User.objects.filter(Q(part__debt=self) | Q(debt=self)):
            user.save()

    def get_debitors(self) -> int:
        """Get number of debitors."""
        return User.objects.filter(part__debt=self).distinct().count()

    def get_parts(self) -> int:
        """Get number of parts."""
        return query_sum(self.part_set, "part", output_field=models.FloatField())


class Part(models.Model):
    """Part of a Debt."""

    debt = models.ForeignKey(Debt, on_delete=models.PROTECT, verbose_name=_("Debt"))
    debitor = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name=_("Debitor")
    )
    part = models.FloatField(_("Part"), default=1)
    value = models.FloatField(_("Value"), default=0)
    description = models.CharField(_("Description"), max_length=1000, blank=True)

    def __str__(self):
        """Describe this Part."""
        return _(
            "Part of %(value).2f € from %(debitor)s for %(debt)s: %(description)s"
        ) % {
            "debt": self.debt,
            "debitor": self.debitor,
            **vars(self),
        }

    class Meta:
        """Meta."""

        verbose_name = _("Part")

    def save(self, *args, allow_recursion=True, **kwargs):
        """Update value."""
        self.value = self.part * self.debt.part_value
        super().save(*args, **kwargs)
        if allow_recursion:
            self.debt.save()

    def get_absolute_url(self) -> str:
        """Url to debt."""
        return self.debt.get_absolute_url()


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
            available = float(self.sum_shares())
            self.ratio = float(self.value) / available if available >= self.value else 0
        super().save(*args, **kwargs)
        for share in self.share_set.all():
            share.save(allow_recursion=False)
        for user in User.objects.filter(Q(share__pool=self) | Q(pool=self)).distinct():
            user.save()

    def real_shares(self):
        """Exclude trivial shares."""
        return self.share_set.exclude(maxi=0)

    def sum_shares(self):
        """Get maxi available amount."""
        return query_sum(self.share_set, "maxi", output_field=models.DecimalField())

    def missing(self):
        """Compute what is missing to reach the value."""
        return self.value - self.sum_shares()


class Share(models.Model):
    """Share of a crowd funding."""

    pool = models.ForeignKey(Pool, on_delete=models.PROTECT, verbose_name=_("Pool"))
    participant = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name=_("Participant")
    )
    maxi = models.DecimalField(_("Maxi"), max_digits=8, decimal_places=2, default=0)
    value = models.FloatField(_("Value"), default=0)

    def __str__(self):
        """Describe this Share."""
        return (
            f"Share of {self.value} / {self.maxi} "
            f"from {self.participant} for {self.pool}"
        )

    class Meta:
        """Meta."""

        unique_together = ["pool", "participant"]
        verbose_name = _("Share")

    def save(self, *args, allow_recursion=True, **kwargs):
        """Update value, and trigger pool update."""
        self.value = float(self.maxi) * self.pool.ratio
        super().save(*args, **kwargs)
        if allow_recursion:
            self.pool.save()

    def get_absolute_url(self) -> str:
        """Return to Pool."""
        return self.pool.get_absolute_url()
