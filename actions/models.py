"""Model to log users actions."""
from json import loads

from django.apps import apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.core.serializers import serialize

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
        return f"{self.user} {self.get_act_display()} {self.item()}"

    def item(self):
        """Get item, if it still exist, or an older serialized version."""
        app_label, model_name = self.json["model"].split(".")
        model = apps.get_model(app_label=app_label, model_name=model_name)
        obj = model.objects.filter(pk=self.json["pk"])
        if obj.exists():
            return obj.first()
        return self.json


def to_json(inst):
    """Serialize a django object."""
    return loads(serialize("json", [inst]))[0]
