"""Filters for compotes querysets."""

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

import django_filters

from .models import Debt


class DebtFilter(django_filters.FilterSet):
    """FilterSet for the Debt model."""

    user = django_filters.CharFilter(label=_("User"), method="user_filter")
    debt = django_filters.CharFilter(label=_("Debt"), method="debt_filter")

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
