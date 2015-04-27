# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Fee'
        db.create_table(u'ratechecker_fee', (
            ('fee_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('plan', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ratechecker.Product'])),
            ('product_id', self.gf('django.db.models.fields.IntegerField')()),
            ('state_id', self.gf('localflavor.us.models.USStateField')(max_length=2)),
            ('lender', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('single_family', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('condo', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('coop', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('origination_dollar', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=4)),
            ('origination_percent', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=3)),
            ('third_party', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=4)),
            ('data_timestamp', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'ratechecker', ['Fee'])

        # Adding unique constraint on 'Fee', fields ['product_id', 'state_id', 'lender', 'single_family', 'condo', 'coop']
        db.create_unique(u'ratechecker_fee', ['product_id', 'state_id', 'lender', 'single_family', 'condo', 'coop'])


    def backwards(self, orm):
        # Removing unique constraint on 'Fee', fields ['product_id', 'state_id', 'lender', 'single_family', 'condo', 'coop']
        db.delete_unique(u'ratechecker_fee', ['product_id', 'state_id', 'lender', 'single_family', 'condo', 'coop'])

        # Deleting model 'Fee'
        db.delete_table(u'ratechecker_fee')


    models = {
        u'ratechecker.adjustment': {
            'Meta': {'object_name': 'Adjustment'},
            'adj_value': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3'}),
            'affect_rate_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'data_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_fico': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'max_loan_amt': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'max_ltv': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3'}),
            'min_fico': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'min_loan_amt': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'min_ltv': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ratechecker.Product']"}),
            'prop_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'rule_id': ('django.db.models.fields.IntegerField', [], {}),
            'state': ('localflavor.us.models.USStateField', [], {'max_length': '2', 'null': 'True'})
        },
        u'ratechecker.fee': {
            'Meta': {'unique_together': "(('product_id', 'state_id', 'lender', 'single_family', 'condo', 'coop'),)", 'object_name': 'Fee'},
            'condo': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'coop': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'data_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'fee_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lender': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'origination_dollar': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '4'}),
            'origination_percent': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ratechecker.Product']"}),
            'product_id': ('django.db.models.fields.IntegerField', [], {}),
            'single_family': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'state_id': ('localflavor.us.models.USStateField', [], {'max_length': '2'}),
            'third_party': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '4'})
        },
        u'ratechecker.product': {
            'Meta': {'object_name': 'Product'},
            'adj_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'ai_value': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4'}),
            'annual_cap': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'arm_index': ('django.db.models.fields.CharField', [], {'max_length': '96', 'null': 'True'}),
            'arm_margin': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4'}),
            'condo': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'coop': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'data_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'int_adj_cap': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'int_adj_term': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'io': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'loan_cap': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'loan_purpose': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'loan_term': ('django.db.models.fields.IntegerField', [], {}),
            'loan_type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'max_fico': ('django.db.models.fields.IntegerField', [], {}),
            'max_loan_amt': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'max_ltv': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3'}),
            'min_fico': ('django.db.models.fields.IntegerField', [], {}),
            'min_loan_amt': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'min_ltv': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3'}),
            'plan_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'pmt_type': ('django.db.models.fields.CharField', [], {'default': "'FIXED'", 'max_length': '12'}),
            'single_family': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'ratechecker.rate': {
            'Meta': {'object_name': 'Rate'},
            'base_rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'data_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'lock': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ratechecker.Product']"}),
            'rate_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'region_id': ('django.db.models.fields.IntegerField', [], {}),
            'total_points': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'})
        },
        u'ratechecker.region': {
            'Meta': {'object_name': 'Region'},
            'data_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'state_id': ('localflavor.us.models.USStateField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['ratechecker']