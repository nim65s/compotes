"""Compotes admin ui."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models

for model in (models.Debt, models.Part, models.Pool, models.Share):
    admin.site.register(model)

admin.site.register(models.User, UserAdmin)
