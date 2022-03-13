"""Compotes forms."""

from django.forms.models import inlineformset_factory

from .models import Debt, Part

DebtPartsFormset = inlineformset_factory(
    Debt, Part, fields=["debitor", "part", "description"]
)
