# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Adjustment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rule_id', models.IntegerField()),
                ('affect_rate_type', models.CharField(max_length=1, choices=[(b'P', b'Points'), (b'R', b'Rate')])),
                ('adj_value', models.DecimalField(null=True, max_digits=6, decimal_places=3)),
                ('min_loan_amt', models.DecimalField(null=True, max_digits=12, decimal_places=2)),
                ('max_loan_amt', models.DecimalField(null=True, max_digits=12, decimal_places=2)),
                ('prop_type', models.CharField(max_length=18, null=True, choices=[(b'CONDO', b'Condo'), (b'COOP', b'Co-op'), (b'CASHOUT-REFI', b'Cash-out refinance')])),
                ('min_fico', models.IntegerField(null=True)),
                ('max_fico', models.IntegerField(null=True)),
                ('min_ltv', models.DecimalField(null=True, max_digits=6, decimal_places=3)),
                ('max_ltv', models.DecimalField(null=True, max_digits=6, decimal_places=3)),
                ('state', localflavor.us.models.USStateField(max_length=2, null=True)),
                ('data_timestamp', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('plan_id', models.IntegerField(serialize=False, primary_key=True)),
                ('institution', models.CharField(max_length=16)),
                ('loan_purpose', models.CharField(max_length=12, choices=[(b'REFI', b'Refinance'), (b'PURCH', b'Purchase')])),
                ('pmt_type', models.CharField(default=b'FIXED', max_length=12, choices=[(b'FIXED', b'Fixed Rate Mortgage'), (b'ARM', b'Adjustable Rate Mortgage')])),
                ('loan_type', models.CharField(max_length=12, choices=[(b'JUMBO', b'Jumbo Mortgage'), (b'CONF', b'Conforming Loan'), (b'AGENCY', b'Agency Loan'), (b'FHA', b'Federal Housing Administration Loan'), (b'VA', b'Veterans Affairs Loan'), (b'VA-HB', b'VA-HB Loan'), (b'FHA-HB', b'FHA-HB Loan')])),
                ('loan_term', models.IntegerField()),
                ('int_adj_term', models.IntegerField(help_text=b'1st part of the ARM definition. E.g. 5 in 5/1 ARM', null=True)),
                ('adj_period', models.PositiveSmallIntegerField(null=True)),
                ('io', models.BooleanField()),
                ('arm_index', models.CharField(max_length=96, null=True)),
                ('int_adj_cap', models.IntegerField(help_text=b'Max percentage points the rate can adjust at first adjustment.', null=True)),
                ('annual_cap', models.IntegerField(help_text=b'Max percentage points adjustable at each subsequent adjustment', null=True)),
                ('loan_cap', models.IntegerField(help_text=b'Total lifetime maximum change that the ARM rate can have.', null=True)),
                ('arm_margin', models.DecimalField(null=True, max_digits=6, decimal_places=4)),
                ('ai_value', models.DecimalField(null=True, max_digits=6, decimal_places=4)),
                ('min_ltv', models.DecimalField(null=True, max_digits=6, decimal_places=3)),
                ('max_ltv', models.DecimalField(null=True, max_digits=6, decimal_places=3)),
                ('min_fico', models.IntegerField()),
                ('max_fico', models.IntegerField()),
                ('min_loan_amt', models.DecimalField(max_digits=12, decimal_places=2)),
                ('max_loan_amt', models.DecimalField(max_digits=12, decimal_places=2)),
                ('single_family', models.BooleanField(default=True)),
                ('condo', models.BooleanField(default=False)),
                ('coop', models.BooleanField(default=False)),
                ('data_timestamp', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Rate',
            fields=[
                ('rate_id', models.IntegerField(serialize=False, primary_key=True)),
                ('region_id', models.IntegerField()),
                ('lock', models.PositiveSmallIntegerField()),
                ('base_rate', models.DecimalField(max_digits=6, decimal_places=3)),
                ('total_points', models.DecimalField(max_digits=6, decimal_places=3)),
                ('data_timestamp', models.DateTimeField()),
                ('product', models.ForeignKey(to='ratechecker.Product')),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('region_id', models.IntegerField(db_index=True)),
                ('state_id', localflavor.us.models.USStateField(max_length=2)),
                ('data_timestamp', models.DateTimeField()),
            ],
        ),
        migrations.AddField(
            model_name='fee',
            name='plan',
            field=models.ForeignKey(to='ratechecker.Product'),
        ),
        migrations.AddField(
            model_name='adjustment',
            name='product',
            field=models.ForeignKey(to='ratechecker.Product'),
        ),
        migrations.AlterUniqueTogether(
            name='fee',
            unique_together=set([('product_id', 'state_id', 'lender', 'single_family', 'condo', 'coop')]),
        ),
    ]
