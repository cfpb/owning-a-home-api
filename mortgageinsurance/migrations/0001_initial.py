# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MonthlyMortgageIns'
        db.create_table(u'mortgageinsurance_monthlymortgageins', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('insurer', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('min_ltv', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=3)),
            ('max_ltv', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=3)),
            ('min_fico', self.gf('django.db.models.fields.IntegerField')()),
            ('max_fico', self.gf('django.db.models.fields.IntegerField')()),
            ('min_loan_term', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=3)),
            ('max_loan_term', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=3)),
            ('pmt_type', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('min_loan_amt', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('max_loan_amt', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('premium', self.gf('django.db.models.fields.DecimalField')(max_digits=5, decimal_places=2)),
        ))
        db.send_create_signal(u'mortgageinsurance', ['MonthlyMortgageIns'])


    def backwards(self, orm):
        # Deleting model 'MonthlyMortgageIns'
        db.delete_table(u'mortgageinsurance_monthlymortgageins')


    models = {
        u'mortgageinsurance.monthlymortgageins': {
            'Meta': {'object_name': 'MonthlyMortgageIns'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'insurer': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'max_fico': ('django.db.models.fields.IntegerField', [], {}),
            'max_loan_amt': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'max_loan_term': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'max_ltv': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'min_fico': ('django.db.models.fields.IntegerField', [], {}),
            'min_loan_amt': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'min_loan_term': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'min_ltv': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'pmt_type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'premium': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '2'})
        }
    }

    complete_apps = ['mortgageinsurance']