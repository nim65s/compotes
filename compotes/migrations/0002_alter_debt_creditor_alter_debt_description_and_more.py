# Generated by Django 4.0.3 on 2022-03-11 19:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("compotes", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="debt",
            name="creditor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
                verbose_name="creditor",
            ),
        ),
        migrations.AlterField(
            model_name="debt",
            name="description",
            field=models.TextField(blank=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="debt",
            name="part_value",
            field=models.FloatField(default=0, verbose_name="part value"),
        ),
        migrations.AlterField(
            model_name="debt",
            name="scribe",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="scribe",
            ),
        ),
        migrations.AlterField(
            model_name="debt",
            name="value",
            field=models.DecimalField(
                decimal_places=2, max_digits=8, verbose_name="value"
            ),
        ),
        migrations.AlterField(
            model_name="part",
            name="debitor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
                verbose_name="debitor",
            ),
        ),
        migrations.AlterField(
            model_name="part",
            name="debt",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="compotes.debt",
                verbose_name="debt",
            ),
        ),
        migrations.AlterField(
            model_name="part",
            name="part",
            field=models.FloatField(default=1, verbose_name="part"),
        ),
        migrations.AlterField(
            model_name="part",
            name="value",
            field=models.FloatField(default=0, verbose_name="value"),
        ),
        migrations.AlterField(
            model_name="pool",
            name="description",
            field=models.TextField(blank=True, verbose_name="description"),
        ),
        migrations.AlterField(
            model_name="pool",
            name="organiser",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
                verbose_name="organiser",
            ),
        ),
        migrations.AlterField(
            model_name="pool",
            name="ratio",
            field=models.FloatField(default=0, verbose_name="ratio"),
        ),
        migrations.AlterField(
            model_name="pool",
            name="value",
            field=models.DecimalField(
                decimal_places=2, max_digits=8, verbose_name="value"
            ),
        ),
        migrations.AlterField(
            model_name="share",
            name="maxi",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=8, verbose_name="maxi"
            ),
        ),
        migrations.AlterField(
            model_name="share",
            name="participant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to=settings.AUTH_USER_MODEL,
                verbose_name="participant",
            ),
        ),
        migrations.AlterField(
            model_name="share",
            name="pool",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="compotes.pool",
                verbose_name="pool",
            ),
        ),
        migrations.AlterField(
            model_name="share",
            name="value",
            field=models.FloatField(default=0, verbose_name="value"),
        ),
        migrations.AlterField(
            model_name="user",
            name="balance",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=8, verbose_name="balance"
            ),
        ),
    ]
