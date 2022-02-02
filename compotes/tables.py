"""Compotes Tables."""

import django_tables2 as tables

from .models import Debt, Pool


class DebtTable(tables.Table):
    """List Debts."""

    class Meta:
        """Meta."""

        model = Debt
        attrs = {"class": "table"}
        fields = ["updated", "scribe", "creditor", "value"]
        template_name = "ndh/tables.html"
        ordering = "updated"


class PoolTable(tables.Table):
    """List Pools."""

    class Meta:
        """Meta."""

        model = Pool
        attrs = {"class": "table"}
        fields = ["updated", "organiser", "name", "value"]
        template_name = "ndh/tables.html"
        order_by = "updated"
