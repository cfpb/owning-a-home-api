# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion
import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="County",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "county_fips",
                    models.CharField(
                        help_text="A three-digit FIPS code for the state's county",
                        max_length=3,
                    ),
                ),
                (
                    "county_name",
                    models.CharField(help_text="The county name", max_length=100),
                ),
            ],
            options={"ordering": ["county_fips"],},
        ),
        migrations.CreateModel(
            name="CountyLimit",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "fha_limit",
                    models.DecimalField(
                        help_text="Federal Housing Administration loan lending limit for the county",
                        max_digits=12,
                        decimal_places=2,
                    ),
                ),
                (
                    "gse_limit",
                    models.DecimalField(
                        help_text="Loan limit for mortgages acquired by the Government-Sponsored Enterprises",
                        max_digits=12,
                        decimal_places=2,
                    ),
                ),
                (
                    "va_limit",
                    models.DecimalField(
                        help_text="The Department of Veterans Affairs loan guaranty program limit",
                        max_digits=12,
                        decimal_places=2,
                    ),
                ),
                (
                    "county",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="countylimits.County",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="State",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "state_fips",
                    models.CharField(
                        help_text="A two-digit FIPS code for the state", max_length=2
                    ),
                ),
                (
                    "state_abbr",
                    localflavor.us.models.USStateField(
                        help_text="A two-letter state abbreviation", max_length=2
                    ),
                ),
            ],
            options={"ordering": ["state_fips"],},
        ),
        migrations.AddField(
            model_name="county",
            name="state",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="countylimits.State"
            ),
        ),
    ]
