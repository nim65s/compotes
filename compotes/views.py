"""Compotes views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, FormView, UpdateView
from django.views.generic.edit import BaseUpdateView

from django_tables2 import SingleTableMixin, SingleTableView  # type: ignore
from django_filters.views import FilterView
from ndh.mixins import NDHFormMixin

from .models import Debt, User, Pool, Share
from .forms import DebtPartsFormset
from .tables import DebtTable, PoolTable
from .filters import DebtFilter


class UserListView(LoginRequiredMixin, ListView):
    """Main view."""

    model = User
    ordering = ["balance"]


class DebtListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    """Debt list view."""

    model = Debt
    table_class = DebtTable
    filterset_class = DebtFilter


class DebtCreateView(LoginRequiredMixin, NDHFormMixin, CreateView):
    """Debt create view."""

    model = Debt
    fields = ["creditor", "description", "value"]
    title = _("Add a Debt")

    def form_valid(self, form) -> HttpResponse:
        """Document scribe."""
        form.instance.scribe = self.request.user
        return super().form_valid(form)


class DebtUpdateView(LoginRequiredMixin, NDHFormMixin, UpdateView):
    """Debt update view."""

    model = Debt
    fields = ["creditor", "description", "value"]
    title = _("Edit a debt")

    def form_valid(self, form) -> HttpResponse:
        """Ensure someone is not messing with someone else's debt."""
        if form.instance.scribe != self.request.user:
            raise PermissionDenied(_(f"Only {form.instance.scribe} can edit this."))
        return super().form_valid(form)


class DebtDetailView(LoginRequiredMixin, DetailView):
    """Debt detail view."""

    model = Debt


class PartsUpdateView(LoginRequiredMixin, NDHFormMixin, BaseUpdateView, FormView):
    """Update a debt parts."""

    model = Debt
    template_name = "compotes/parts_form.html"
    continue_edit = True

    def get_form(self, form_class=None):
        """Instanciate the Debt/Parts formset."""
        return DebtPartsFormset(**self.get_form_kwargs())

    def form_valid(self, form):
        """Save the form without overriding self.object and conclude."""
        form.save()
        return HttpResponseRedirect(self.get_success_url())


class PoolCreateView(LoginRequiredMixin, NDHFormMixin, CreateView):
    """Pool create view."""

    model = Pool
    fields = ["name", "description", "value"]
    title = _("Add a Pool")

    def form_valid(self, form) -> HttpResponse:
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
    title = _("Edit a pool")

    def form_valid(self, form) -> HttpResponse:
        """Ensure someone is not messing with someone else's debt."""
        if form.instance.organiser != self.request.user:
            raise PermissionDenied(_(f"Only {form.instance.organiser} can edit this."))
        return super().form_valid(form)


class ShareUpdateView(LoginRequiredMixin, NDHFormMixin, UpdateView):
    """Share update view."""

    model = Share
    fields = ["maxi"]
    title = _("Edit my share")

    def get_object(self, queryset=None) -> Share:
        """Instanciate the Debt/Parts formset."""
        pool = get_object_or_404(Pool, slug=self.kwargs.get(self.slug_url_kwarg))
        return Share.objects.get_or_create(pool=pool, participant=self.request.user)[0]


class PoolListView(LoginRequiredMixin, SingleTableView):
    """Debt list view."""

    model = Pool
    table_class = PoolTable

    def get_queryset(self) -> QuerySet:
        """Show only those the user knows."""
        return self.model.objects.filter(
            Q(organiser=self.request.user) | Q(share__participant=self.request.user)
        ).distinct()
