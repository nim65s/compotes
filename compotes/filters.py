"""Filters for compotes querysets."""

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

import django_filters

from .models import Debt


class DebtFilter(django_filters.FilterSet):
    """FilterSet for the Debt model."""

    user = django_filters.CharFilter(label=_("User"), method="user_filter")

    class Meta:
        """Meta."""

        model = Debt
        fields = ["user"]

    def user_filter(self, queryset, name, value):
        """Filter debt by username."""
        return queryset.filter(
            Q(creditor__username__icontains=value)
            | Q(part__debitor__username__icontains=value)
        ).distinct()
