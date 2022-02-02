"""Compotes views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView, FormView, UpdateView
from django.views.generic.edit import BaseUpdateView

from django_tables2 import SingleTableView
from ndh.mixins import NDHFormMixin

from .models import Debt, User, Pool
from .forms import DebtPartsFormset
from .tables import DebtTable


class UserListView(LoginRequiredMixin, ListView):
    """Main view."""

    model = User
    ordering = ["balance"]


class DebtListView(LoginRequiredMixin, SingleTableView):
    """Debt list view."""

    model = Debt
    ordering = ["updated"]
    table_class = DebtTable


class DebtCreateView(LoginRequiredMixin, NDHFormMixin, CreateView):
    """Debt create view."""

    model = Debt
    fields = ["creditor", "value"]
    title = "Add a debt"

    def form_valid(self, form):
        """Document scribe."""
        form.instance.scribe = self.request.user
        return super().form_valid(form)


class DebtUpdateView(LoginRequiredMixin, NDHFormMixin, UpdateView):
    """Debt update view."""

    model = Debt
    fields = ["creditor", "value"]
    title = "Update a debt"

    def form_valid(self, form):
        """Ensure someone is not messing with someone else's debt."""
        if form.instance.scribe != self.request.user:
            raise PermissionDenied(f"Only {form.instance.scribe} can edit this.")
        return super().form_valid(form)


class DebtDetailView(LoginRequiredMixin, DetailView):
    """Debt detail view."""

    model = Debt


class PartsUpdateView(LoginRequiredMixin, BaseUpdateView, FormView):
    """Update a debt parts."""

    model = Debt
    template_name = "compotes/parts_form.html"

    def get_form(self, form_class=None):
        """Instanciate the Debt/Parts formset."""
        return DebtPartsFormset(**self.get_form_kwargs())

    def form_valid(self, form):
        """Save the form without overriding self.object and conclude."""
        form.save()
        self.object.update()
        return HttpResponseRedirect(self.object.get_absolute_url())


class PoolCreateView(LoginRequiredMixin, NDHFormMixin, CreateView):
    """Pool create view."""

    model = Pool
    fields = ["name", "description", "value"]
    title = "Add a pool"

    def form_valid(self, form):
        """Document organiser."""
        form.instance.organiser = self.request.user
        return super().form_valid(form)


class PoolDetailView(LoginRequiredMixin, DetailView):
    """Pool detail view."""

    model = Pool


class PoolUpdateView(LoginRequiredMixin, NDHFormMixin, UpdateView):
    """Pool update view."""

    model = Pool
    fields = ["name", "description", "value"]
    title = "Update a pool"

    def form_valid(self, form):
        """Ensure someone is not messing with someone else's debt."""
        if form.instance.organiser != self.request.user:
            raise PermissionDenied(f"Only {form.instance.organiser} can edit this.")
        return super().form_valid(form)
