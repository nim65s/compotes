# Generated by Django 4.1 on 2022-09-05 20:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("compotes", "0013_drop_scribe"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="debt",
            name="scribe",
        ),
    ]
