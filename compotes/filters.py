"""Filters for compotes querysets."""

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

import django_filters
from ndh.forms import DatalistField

from .models import Debt, User


def get_users():
    """Get the dict of all users by username and representation."""
    return {u.username: repr(u) for u in User.objects.all()}


class DatalistFilter(django_filters.Filter):
    """A Filter with DatalistField."""

    field_class = DatalistField


class DebtFilter(django_filters.FilterSet):
    """FilterSet for the Debt model."""

    user = DatalistFilter(
        label=_("User"),
        help_text=_("Filter by Creditor and/or Debitor"),
        method="user_filter",
        datalist=get_users,
    )
    debt = django_filters.CharFilter(
        label=_("Debt"),
        help_text=_("Search in Debt name and/and description"),
        method="debt_filter",
    )

    class Meta:
        """Meta."""

        model = Debt
        fields = ["user", "debt"]

    def user_filter(self, queryset, name, value):
        """Filter debts by creditor / debitor username."""
        return queryset.filter(
            Q(creditor__username__icontains=value)
            | Q(creditor__last_name__icontains=value)
            | Q(creditor__first_name__icontains=value)
            | Q(part__debitor__username__icontains=value)
            | Q(part__debitor__last_name__icontains=value)
            | Q(part__debitor__first_name__icontains=value)
        ).distinct()

    def debt_filter(self, queryset, nam, value):
        """Filter debts by name / description."""
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )
