"""Compotes views."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, SingleTableView  # type: ignore
from ndh.mixins import NDHDeleteMixin, NDHFormMixin

from actions.models import Action, to_json
from actions.views import ActionCreateMixin, ActionDeleteMixin, ActionUpdateMixin

from .filters import DebtFilter
from .forms import DebtForm, EventForm, PartForm, ShareForm
from .models import Debt, Event, Part, Pool, Share, User
from .tables import DebtTable, EventTable, PoolTable, UserTable


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
                "class": lambda record: (
                    "table-primary" if record == self.request.user else ""
                ),
            },
        }


class UserDetailView(LoginRequiredMixin, DetailView):
    """Debt detail view."""

    model = User


class EventListView(LoginRequiredMixin, SingleTableView):
    """Event list view."""

    model = Event
    table_class = EventTable

    def get_queryset(self) -> QuerySet:
        """Show only events the user organises or has debts in."""
        user = self.request.user
        return self.model.objects.filter(
            Q(organiser=user) | Q(debt__creditor=user) | Q(debt__part__debitor=user),
        ).distinct()


class EventCreateView(LoginRequiredMixin, NDHFormMixin, ActionCreateMixin, CreateView):
    """Event create view."""

    model = Event
    form_class = EventForm
    title = _("Add an Event")

    def form_valid(self, form) -> HttpResponse:
        """Document organiser."""
        form.instance.organiser = self.request.user
        return super().form_valid(form)


class EventDetailView(LoginRequiredMixin, DetailView):
    """Event detail view."""

    model = Event

    def get_context_data(self, **kwargs):
        """Add per-participant balances and related actions."""
        balances = [
            (user, user.get_event_balance(self.object))
            for user in self.object.participants()
        ]
        actions = Action.objects.filter(
            Q(json__model="compotes.event", json__pk=self.object.pk)
            | Q(json__model="compotes.debt", json__fields__event=self.object.pk),
        )
        return super().get_context_data(
            balances=balances,
            unsettled=any(balance for _user, balance in balances),
            actions=actions,
            **kwargs,
        )


class EventUpdateView(LoginRequiredMixin, NDHFormMixin, ActionUpdateMixin, UpdateView):
    """Event update view."""

    model = Event
    form_class = EventForm
    title = _("Edit an event")


class EventCloseView(LoginRequiredMixin, SingleObjectMixin, View):
    """Close an Event, requiring confirmation if balances aren't settled."""

    model = Event

    def post(self, request, *args, **kwargs) -> HttpResponse:
        """Fold leftover balances into the global pool, once confirmed."""
        event = self.get_object()
        unsettled = [
            user for user in event.participants() if user.get_event_balance(event) != 0
        ]
        if unsettled and not request.POST.get("confirm"):
            messages.warning(
                request,
                _(
                    "Some balances are not settled yet: check the "
                    "confirmation box to close anyway.",
                ),
            )
            return redirect(event.get_absolute_url())
        event.close()
        Action.objects.create(
            user=request.user,
            act=Action.Act.UPDATE,
            json=to_json(event),
        )
        return redirect(event.get_absolute_url())


class EventReopenView(LoginRequiredMixin, SingleObjectMixin, View):
    """Reopen a closed Event, isolating its Debts from the global balance again."""

    model = Event

    def post(self, request, *args, **kwargs) -> HttpResponse:
        """Reopen the Event."""
        event = self.get_object()
        event.reopen()
        Action.objects.create(
            user=request.user,
            act=Action.Act.UPDATE,
            json=to_json(event),
        )
        return redirect(event.get_absolute_url())


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
        """Add a Part form to create one, and related actions."""
        actions = Action.objects.filter(
            Q(json__model="compotes.part", json__fields__debt=self.object.pk)
            | Q(json__model="compotes.debt", json__pk=self.object.pk),
        )
        return super().get_context_data(actions=actions, form=PartForm(), **kwargs)


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

    def form_valid(self, form):
        """Update balance."""
        debt = self.object.debt
        debitor = self.object.debitor
        ret = super().form_valid(form)
        debitor.save()
        debt.save()
        return ret


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

    def get_context_data(self, **kwargs):
        """Add related actions."""
        share = Share.objects.filter(pool=self.object, participant=self.request.user)
        form = ShareForm(
            initial={"maxi": share.first().maxi} if share.exists() else None,
        )
        actions = Action.objects.filter(
            Q(json__model="compotes.pool", json__pk=self.object.pk)
            | Q(json__model="compotes.share", json__fields__pool=self.object.pk),
        )
        return super().get_context_data(actions=actions, form=form, **kwargs)


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
            Q(organiser=self.request.user) | Q(share__participant=self.request.user),
        ).distinct()
