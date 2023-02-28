"""Model to log users actions."""
from json import loads

from django.apps import apps
from django.conf import settings
from django.core.serializers import serialize
from django.db import models
from django.utils.translation import gettext_lazy as _

from ndh.models import TimeStampedModel


class Action(TimeStampedModel):
    """Log users actions on other models."""

    class Act(models.TextChoices):
        """CRUD without the R."""

        CREATE = "C", _("created")
        UPDATE = "U", _("updated")
        DELETE = "D", _("deleted")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    act = models.CharField(max_length=1, choices=Act.choices)
    json = models.JSONField()

    def __str__(self):
        """Describe this action."""
        return _("%(user)s %(act)s %(item)s") % {
            "user": self.user,
            "act": self.get_act_display(),
            "item": self.item(),
        }

    @property
    def emoji(self):
        """Act → Emoji."""
        if self.act == "C":
            return "\u2795"
        if self.act == "U":
            return "✏️"
        return "❌"

    @property
    def verbose_name(self):
        """Get the model's verbose name."""
        return self.model()._meta.verbose_name

    def model(self):
        """Return the Model."""
        app_label, model_name = self.json["model"].split(".")
        return apps.get_model(app_label=app_label, model_name=model_name)

    def item(self):
        """Get item, if it still exist, or an older serialized version."""
        obj = self.model().objects.filter(pk=self.json["pk"])
        if obj.exists():
            return obj.first()
        return self.json


def to_json(inst):
    """Serialize a django object."""
    return loads(serialize("json", [inst]))[0]
