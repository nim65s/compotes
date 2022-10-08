"""Compotes views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView

from django_tables2 import SingleTableMixin, SingleTableView  # type: ignore
from django_filters.views import FilterView
from ndh.mixins import NDHFormMixin, NDHDeleteMixin

# from actions.models import Action, to_json
from actions.views import ActionCreateMixin, ActionUpdateMixin, ActionDeleteMixin

from .models import Debt, User, Pool, Share, Part
from .forms import DebtForm, PartForm
from .tables import DebtTable, PoolTable, UserTable
from .filters import DebtFilter


class UserListView(LoginRequiredMixin, SingleTableView):
    """Main view."""

    model = User
    table_class = UserTable

    def get_queryset(self):
        """Exclude other users with a balance of 0."""
        exclude = Q(balance=0) & ~Q(pk=self.request.user.pk)
        return super().get_queryset().exclude(exclude)

    def get_table_kwargs(self):
        """Color current user row."""
        return {
            "row_attrs": {
                "class": lambda record: "table-primary"
                if record == self.request.user
                else ""
            }
        }


class UserDetailView(LoginRequiredMixin, DetailView):
    """Debt detail view."""

    model = User


class DebtListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    """Debt list view."""

    model = Debt
    table_class = DebtTable
    filterset_class = DebtFilter

    def get_context_data(self, **kwargs):
        """Add list of users to allow simple autocompletion in search field."""
        return super().get_context_data(users=User.objects.all(), **kwargs)


class DebtCreateView(LoginRequiredMixin, NDHFormMixin, ActionCreateMixin, CreateView):
    """Debt create view."""

    model = Debt
    form_class = DebtForm
    title = _("Add a Debt")


class DebtUpdateView(LoginRequiredMixin, NDHFormMixin, ActionUpdateMixin, UpdateView):
    """Debt update view."""

    model = Debt
    form_class = DebtForm
    title = _("Edit a debt")


class DebtDetailView(LoginRequiredMixin, DetailView):
    """Debt detail view."""

    model = Debt

    def get_context_data(self, **kwargs):
        """Add a Part form to create one."""
        return super().get_context_data(form=PartForm(), **kwargs)


class PartCreateView(LoginRequiredMixin, ActionCreateMixin, CreateView):
    """Create a Part."""

    model = Part
    fields = ["debitor", "part", "description"]

    def form_valid(self, form) -> HttpResponse:
        """Set Debt."""
        form.instance.debt = get_object_or_404(Debt, pk=self.kwargs["pk"])
        return super().form_valid(form)


class PartUpdateView(LoginRequiredMixin, NDHFormMixin, ActionUpdateMixin, UpdateView):
    """Update a Part."""

    model = Part
    fields = ["debitor", "part", "description"]


class PartDeleteView(LoginRequiredMixin, NDHDeleteMixin, ActionDeleteMixin, DeleteView):
    """Delete a Part."""

    model = Part

    def get_success_url(self):
        """Return to Debt."""
        return self.object.get_absolute_url()


class PoolCreateView(LoginRequiredMixin, NDHFormMixin, ActionCreateMixin, CreateView):
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


class PoolUpdateView(LoginRequiredMixin, NDHFormMixin, ActionUpdateMixin, UpdateView):
    """Pool update view."""

    model = Pool
    fields = ["name", "description", "value"]
    title = _("Edit a pool")


class ShareUpdateView(LoginRequiredMixin, NDHFormMixin, ActionUpdateMixin, UpdateView):
    """Share update view."""

    model = Share
    fields = ["maxi"]
    title = _("Edit my share")

    def get_object(self, queryset=None) -> Share:
        """Get (and the share object, creating if necessary."""
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
