"""Compotes forms."""

from django.forms import ModelForm
from django.forms.models import inlineformset_factory
from django.utils import timezone

from ndh.forms import AccessibleDateTimeField

from .models import Debt, Part

DebtPartsFormset = inlineformset_factory(
    Debt, Part, fields=["debitor", "part", "description"]
)


class DebtForm(ModelForm):
    """Form for Debts."""

    date = AccessibleDateTimeField(initial=timezone.now)

    class Meta:
        """Meta."""

        model = Debt
        fields = ["name", "date", "creditor", "description", "value"]
