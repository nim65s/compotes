# Generated by Django 4.1 on 2022-08-29 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("compotes", "0007_alter_debt_creditor_alter_debt_description_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="debt",
            name="name",
            field=models.CharField(
                default="CHANGE-ME", max_length=200, verbose_name="Name"
            ),
            preserve_default=False,
        ),
    ]
