"""Compotes forms."""

from django.forms import ModelForm
from django.utils import timezone

from ndh.forms import AccessibleDateTimeField

from .models import Debt, Event, Part, Share


class EventForm(ModelForm):
    """Form for Events."""

    class Meta:
        """Meta."""

        model = Event
        fields = ["name", "description"]


class DebtForm(ModelForm):
    """Form for Debts."""

    date = AccessibleDateTimeField(initial=timezone.now)

    class Meta:
        """Meta."""

        model = Debt
        fields = ["name", "date", "creditor", "event", "description", "value"]


class PartForm(ModelForm):
    """Form for Parts."""

    class Meta:
        """Meta."""

        model = Part
        fields = ["debitor", "part", "description"]


class ShareForm(ModelForm):
    """Form for Share."""

    class Meta:
        """Meta."""

        model = Share
        fields = ["maxi"]
