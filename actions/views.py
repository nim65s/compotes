"""Action Mixins."""

from django.http import HttpResponse

from actions.models import Action, to_json


class ActionMixin:
    """Generic Action Mixin."""

    def form_valid(self, form) -> HttpResponse:
        """Log this action."""
        ret = super().form_valid(form)
        Action.objects.create(
            user=self.request.user,
            act=self.act,
            json=to_json(self.object),
        )
        return ret


class ActionCreateMixin(ActionMixin):
    """Action mixin for Created objects."""

    act = "C"


class ActionUpdateMixin(ActionMixin):
    """Action mixin for Updated objects."""

    act = "U"


class ActionDeleteMixin(ActionMixin):
    """Action mixin for Deleted objects."""

    act = "D"
