"""Compotes admin ui."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from . import models


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    """Add balance to UserAdmin.list_display."""

    list_display = (*BaseUserAdmin.list_display, "balance", "respo")
    fieldsets = (*BaseUserAdmin.fieldsets, ("compotes", {"fields": ("respo",)}))

    def get_urls(self):
        """Add update_balance url."""
        return [
            path("update-balance", self.admin_site.admin_view(self.update_balance)),
            *super().get_urls(),
        ]

    def update_balance(self, request):  # pragma: no cover
        """View to update balances."""
        for user in models.User.objects.all():
            user.save()
        return HttpResponseRedirect(reverse("admin:compotes_user_changelist"))


for model in (models.Debt, models.Part, models.Pool, models.Share):
    admin.site.register(model)
