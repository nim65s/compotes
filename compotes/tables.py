"""Compotes Tables."""

import django_tables2 as tables

from .models import Debt, Pool

END = {"th": {"class": "text-end"}, "td": {"class": "text-end"}}
NBR = {"th": {"class": "text-end"}, "td": {"class": "nombre"}}
EUR = {"th": {"class": "text-end"}, "td": {"class": "euro"}}


class DebtTable(tables.Table):
    """List Debts."""

    debitors = tables.Column(accessor="get_debitors", orderable=False)
    value = tables.Column(attrs=EUR)
    part_value = tables.Column(attrs=EUR)
    link = tables.Column(accessor="get_link", orderable=False, attrs=END)

    class Meta:
        """Meta."""

        model = Debt
        attrs = {"class": "table"}
        fields = [
            "updated",
            "scribe",
            "creditor",
            "debitors",
            "value",
            "part_value",
            "link",
        ]
        template_name = "ndh/tables.html"
        ordering = "updated"

    def render_part_value(self, value):
        """Format .2f."""
        return f"{value:.2f}"


class PoolTable(tables.Table):
    """List Pools."""

    value = tables.Column(attrs=EUR)
    ratio = tables.Column(attrs=NBR)
    link = tables.Column(accessor="get_link", orderable=False, attrs=END)

    class Meta:
        """Meta."""

        model = Pool
        attrs = {"class": "table"}
        fields = ["updated", "organiser", "value", "ratio", "link"]
        template_name = "ndh/tables.html"
        order_by = "updated"

    def render_ratio(self, value):
        """Format .3f."""
        return f"{value:.3f}"
