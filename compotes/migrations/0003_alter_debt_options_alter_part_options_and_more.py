# Generated by Django 4.0.3 on 2022-03-11 21:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("compotes", "0002_alter_debt_creditor_alter_debt_description_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="debt",
            options={"verbose_name": "Debt"},
        ),
        migrations.AlterModelOptions(
            name="part",
            options={"verbose_name": "Part"},
        ),
        migrations.AlterModelOptions(
            name="pool",
            options={"verbose_name": "Pool"},
        ),
        migrations.AlterModelOptions(
            name="share",
            options={"verbose_name": "Share"},
        ),
        migrations.AlterModelOptions(
            name="user",
            options={"ordering": ["username"], "verbose_name": "User"},
        ),
    ]