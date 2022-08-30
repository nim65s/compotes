"""Compotes admin ui."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from . import models


class UserAdmin(BaseUserAdmin):
    """Add balance to UserAdmin.list_display."""

    list_display = list(BaseUserAdmin.list_display) + ["balance"]


for model in (models.Debt, models.Part, models.Pool, models.Share):
    admin.site.register(model)


admin.site.register(models.User, UserAdmin)
