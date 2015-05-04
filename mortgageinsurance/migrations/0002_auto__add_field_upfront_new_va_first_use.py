# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Upfront.new_va_first_use'
        db.add_column(u'mortgageinsurance_upfront', 'new_va_first_use',
                      self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Upfront.new_va_first_use'
        db.delete_column(u'mortgageinsurance_upfront', 'new_va_first_use')


    models = {
        u'mortgageinsurance.monthly': {
            'Meta': {'object_name': 'Monthly'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'insurer': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'loan_term': ('django.db.models.fields.IntegerField', [], {}),
            'max_fico': ('django.db.models.fields.IntegerField', [], {}),
            'max_loan_amt': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'max_ltv': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'min_fico': ('django.db.models.fields.IntegerField', [], {}),
            'min_loan_amt': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'min_ltv': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'pmt_type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'premium': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'})
        },
        u'mortgageinsurance.upfront': {
            'Meta': {'object_name': 'Upfront'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loan_type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'max_ltv': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'min_ltv': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'new_va_first_use': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'premium': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'va_first_use': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'va_status': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'})
        }
    }

    complete_apps = ['mortgageinsurance']