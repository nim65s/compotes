"""Compotes Tables."""

import django_tables2 as tables  # type: ignore
from django.utils.translation import gettext_lazy as _

from .models import Debt, Pool, User

END, NBR, EUR = (
    {"th": {"class": "text-end"}, "td": {"class": cls}}
    for cls in ("text-end", "nombre", "euro")
)


class UserTable(tables.Table):
    """List Users."""

    balance = tables.Column(attrs=EUR)
    user = tables.Column(
        accessor="get_link", order_by="username", verbose_name=_("User")
    )

    class Meta:
        """Meta."""

        model = User
        attrs = {"class": "table"}
        fields = ["balance", "user"]
        template_name = "ndh/tables.html"
        order_by = "balance"


class DebtTable(tables.Table):
    """List Debts."""

    debitors = tables.Column(
        accessor="get_debitors", orderable=False, verbose_name=_("Debitors")
    )
    parts = tables.Column(
        accessor="get_parts", orderable=False, verbose_name=_("Parts")
    )
    value = tables.Column(attrs=EUR)
    part_value = tables.Column(attrs=EUR)
    link = tables.Column(accessor="get_link", orderable=False, verbose_name=_("Link"))

    class Meta:
        """Meta."""

        model = Debt
        attrs = {"class": "table"}
        fields = [
            "link",
            "date",
            "updated",
            "creditor",
            "debitors",
            "parts",
            "value",
            "part_value",
        ]
        template_name = "ndh/tables.html"
        order_by = "-date"

    def render_part_value(self, value) -> str:
        """Format .2f."""
        return f"{value:.2f}"


class PoolTable(tables.Table):
    """List Pools."""

    value = tables.Column(attrs=EUR)
    ratio = tables.Column(attrs=NBR)
    link = tables.Column(accessor="get_link", orderable=False, verbose_name=_("Link"))

    class Meta:
        """Meta."""

        model = Pool
        attrs = {"class": "table"}
        fields = ["link", "updated", "organiser", "value", "ratio"]
        template_name = "ndh/tables.html"
        order_by = "updated"
        row_attrs = {
            "class": lambda record: "table-warning" if record.ratio == 0 else ""
        }

    def render_ratio(self, value) -> str:
        """Format .3f."""
        return f"{value:.3f}"
