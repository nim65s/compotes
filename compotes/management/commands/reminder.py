"""Reminder management command."""

from django.core.management.base import BaseCommand

from compotes.models import User


class Command(BaseCommand):
    """Reminder management command."""

    help = "run User.reminder() for all users"

    def handle(self, *args, **options):
        """Reminder management command."""
        for user in User.objects.all():
            user.reminder()
