"""Compotes Tables."""

import django_tables2 as tables  # type: ignore
from django.utils.translation import gettext_lazy as _

from .models import Debt, Pool

END, NBR, EUR = (
    {"th": {"class": "text-end"}, "td": {"class": cls}}
    for cls in ("text-end", "nombre", "euro")
)


class DebtTable(tables.Table):
    """List Debts."""

    debitors = tables.Column(
        accessor="get_debitors", orderable=False, verbose_name=_("debitors")
    )
    value = tables.Column(attrs=EUR)
    part_value = tables.Column(attrs=EUR)
    link = tables.Column(
        accessor="get_link", orderable=False, attrs=END, verbose_name=_("link")
    )

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
    link = tables.Column(
        accessor="get_link", orderable=False, attrs=END, verbose_name=_("link")
    )

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
