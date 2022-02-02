"""Compotes Tables."""

import django_tables2 as tables

from .models import Debt


class DebtTable(tables.Table):
    """List Debts."""

    class Meta:
        """Meta."""

        model = Debt
        attrs = {"class": "table"}
        fields = ["updated", "scribe", "creditor", "value"]
        template_name = "ndh/tables.html"
