"""Compotes views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import User


class UserListView(LoginRequiredMixin, ListView):
    """Main view."""

    model = User
    ordering = ["balance"]
