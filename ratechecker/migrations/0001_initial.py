# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion
import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Adjustment",
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
                ("rule_id", models.IntegerField()),
                (
                    "affect_rate_type",
                    models.CharField(
                        max_length=1, choices=[("P", "Points"), ("R", "Rate")]
                    ),
                ),
                (
                    "adj_value",
                    models.DecimalField(null=True, max_digits=6, decimal_places=3),
                ),
                (
                    "min_loan_amt",
                    models.DecimalField(null=True, max_digits=12, decimal_places=2),
                ),
                (
                    "max_loan_amt",
                    models.DecimalField(null=True, max_digits=12, decimal_places=2),
                ),
                (
                    "prop_type",
                    models.CharField(
                        max_length=18,
                        null=True,
                        choices=[
                            ("CONDO", "Condo"),
                            ("COOP", "Co-op"),
                            ("CASHOUT-REFI", "Cash-out refinance"),
                        ],
                    ),
                ),
                ("min_fico", models.IntegerField(null=True)),
                ("max_fico", models.IntegerField(null=True)),
                (
                    "min_ltv",
                    models.DecimalField(null=True, max_digits=6, decimal_places=3),
                ),
                (
                    "max_ltv",
                    models.DecimalField(null=True, max_digits=6, decimal_places=3),
                ),
                ("state", localflavor.us.models.USStateField(max_length=2, null=True)),
                ("data_timestamp", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="Fee",
            fields=[
                ("fee_id", models.AutoField(serialize=False, primary_key=True)),
                ("product_id", models.IntegerField()),
                ("state_id", localflavor.us.models.USStateField(max_length=2)),
                ("lender", models.CharField(max_length=16)),
                ("single_family", models.BooleanField(default=True)),
                ("condo", models.BooleanField(default=False)),
                ("coop", models.BooleanField(default=False)),
                (
                    "origination_dollar",
                    models.DecimalField(max_digits=8, decimal_places=2),
                ),
                (
                    "origination_percent",
                    models.DecimalField(max_digits=6, decimal_places=3),
                ),
                ("third_party", models.DecimalField(max_digits=8, decimal_places=2)),
                ("data_timestamp", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("plan_id", models.IntegerField(serialize=False, primary_key=True)),
                ("institution", models.CharField(max_length=16)),
                (
                    "loan_purpose",
                    models.CharField(
                        max_length=12,
                        choices=[("REFI", "Refinance"), ("PURCH", "Purchase")],
                    ),
                ),
                (
                    "pmt_type",
                    models.CharField(
                        default="FIXED",
                        max_length=12,
                        choices=[
                            ("FIXED", "Fixed Rate Mortgage"),
                            ("ARM", "Adjustable Rate Mortgage"),
                        ],
                    ),
                ),
                (
                    "loan_type",
                    models.CharField(
                        max_length=12,
                        choices=[
                            ("JUMBO", "Jumbo Mortgage"),
                            ("CONF", "Conforming Loan"),
                            ("AGENCY", "Agency Loan"),
                            ("FHA", "Federal Housing Administration Loan"),
                            ("VA", "Veterans Affairs Loan"),
                            ("VA-HB", "VA-HB Loan"),
                            ("FHA-HB", "FHA-HB Loan"),
                        ],
                    ),
                ),
                ("loan_term", models.IntegerField()),
                (
                    "int_adj_term",
                    models.IntegerField(
                        help_text="1st part of the ARM definition. E.g. 5 in 5/1 ARM",
                        null=True,
                    ),
                ),
                ("adj_period", models.PositiveSmallIntegerField(null=True)),
                ("io", models.BooleanField()),
                ("arm_index", models.CharField(max_length=96, null=True)),
                (
                    "int_adj_cap",
                    models.IntegerField(
                        help_text="Max percentage points the rate can adjust at first adjustment.",
                        null=True,
                    ),
                ),
                (
                    "annual_cap",
                    models.IntegerField(
                        help_text="Max percentage points adjustable at each subsequent adjustment",
                        null=True,
                    ),
                ),
                (
                    "loan_cap",
                    models.IntegerField(
                        help_text="Total lifetime maximum change that the ARM rate can have.",
                        null=True,
                    ),
                ),
                (
                    "arm_margin",
                    models.DecimalField(null=True, max_digits=6, decimal_places=4),
                ),
                (
                    "ai_value",
                    models.DecimalField(null=True, max_digits=6, decimal_places=4),
                ),
                (
                    "min_ltv",
                    models.DecimalField(null=True, max_digits=6, decimal_places=3),
                ),
                (
                    "max_ltv",
                    models.DecimalField(null=True, max_digits=6, decimal_places=3),
                ),
                ("min_fico", models.IntegerField()),
                ("max_fico", models.IntegerField()),
                ("min_loan_amt", models.DecimalField(max_digits=12, decimal_places=2)),
                ("max_loan_amt", models.DecimalField(max_digits=12, decimal_places=2)),
                ("single_family", models.BooleanField(default=True)),
                ("condo", models.BooleanField(default=False)),
                ("coop", models.BooleanField(default=False)),
                ("data_timestamp", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="Rate",
            fields=[
                ("rate_id", models.IntegerField(serialize=False, primary_key=True)),
                ("region_id", models.IntegerField()),
                ("lock", models.PositiveSmallIntegerField()),
                ("base_rate", models.DecimalField(max_digits=6, decimal_places=3)),
                ("total_points", models.DecimalField(max_digits=6, decimal_places=3)),
                ("data_timestamp", models.DateTimeField()),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ratechecker.Product",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Region",
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
                ("region_id", models.IntegerField(db_index=True)),
                ("state_id", localflavor.us.models.USStateField(max_length=2)),
                ("data_timestamp", models.DateTimeField()),
            ],
        ),
        migrations.AddField(
            model_name="fee",
            name="plan",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="ratechecker.Product"
            ),
        ),
        migrations.AddField(
            model_name="adjustment",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="ratechecker.Product"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="fee",
            unique_together=set(
                [("product_id", "state_id", "lender", "single_family", "condo", "coop")]
            ),
        ),
    ]
