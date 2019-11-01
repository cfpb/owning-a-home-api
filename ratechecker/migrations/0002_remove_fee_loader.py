# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-10-31 16:33
from __future__ import unicode_literals

from django.db import migrations, OperationalError, ProgrammingError

def fix_fee_product_index(apps, schema_editor):
    try:
        schema_editor.execute(
            'DROP INDEX IF EXISTS idx_16977_product_id;'
        )
    except (ProgrammingError, OperationalError):
        pass
    try:
        schema_editor.execute(
            'ALTER TABLE IF EXISTS cfpb.ratechecker_fee '
            'DROP CONSTRAINT IF EXISTS idx_16977_product_id;'
        )
    except (ProgrammingError, OperationalError):
        pass
    try:
        schema_editor.execute(
            'ALTER TABLE IF EXISTS cfpb.ratechecker_fee '
            'ADD CONSTRAINT idx_16977_product_id '
            'UNIQUE (product_id, state_id, lender, single_family, condo, coop);'
        )
    except (ProgrammingError, OperationalError):
        pass

class Migration(migrations.Migration):

    dependencies = [
        ('ratechecker', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='fee',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='fee',
            name='plan',
        ),
        migrations.RunPython(fix_fee_product_index),
        migrations.DeleteModel(
            name='Fee',
        ),
    ]
