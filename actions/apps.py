"""Action tracking."""
from django.apps import AppConfig


class ActionsConfig(AppConfig):
    """Action app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "actions"
