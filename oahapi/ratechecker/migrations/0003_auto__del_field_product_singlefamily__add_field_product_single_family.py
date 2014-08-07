# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Product.singlefamily'
        db.delete_column(u'ratechecker_product', 'singlefamily')

        # Adding field 'Product.single_family'
        db.add_column(u'ratechecker_product', 'single_family',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Product.singlefamily'
        db.add_column(u'ratechecker_product', 'singlefamily',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Deleting field 'Product.single_family'
        db.delete_column(u'ratechecker_product', 'single_family')


    models = {
        u'ratechecker.adjustment': {
            'Meta': {'object_name': 'Adjustment'},
            'adj_value': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3'}),
            'affect_rate_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'data_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'max_fico': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'max_loan_amt': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'max_ltv': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'min_fico': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'min_loan_amt': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2'}),
            'min_ltv': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ratechecker.Product']"}),
            'prop_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'rule_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True'})
        },
        u'ratechecker.product': {
            'Meta': {'object_name': 'Product'},
            'adj_period': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'ai_value': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4'}),
            'annual_cap': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'arm_index': ('django.db.models.fields.CharField', [], {'max_length': '96', 'null': 'True'}),
            'arm_margin': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4'}),
            'condo': ('django.db.models.fields.BooleanField', [], {}),
            'coop': ('django.db.models.fields.BooleanField', [], {}),
            'data_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'institution': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'int_adj_cap': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'int_adj_term': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'io': ('django.db.models.fields.BooleanField', [], {}),
            'loan_cap': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'loan_purpose': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'loan_term': ('django.db.models.fields.IntegerField', [], {}),
            'loan_type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'max_fico': ('django.db.models.fields.IntegerField', [], {}),
            'max_loan_amt': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'max_ltv': ('django.db.models.fields.FloatField', [], {}),
            'min_fico': ('django.db.models.fields.IntegerField', [], {}),
            'min_loan_amt': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'min_ltv': ('django.db.models.fields.FloatField', [], {}),
            'plan_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'pmt_type': ('django.db.models.fields.CharField', [], {'default': "'FIXED'", 'max_length': '12'}),
            'single_family': ('django.db.models.fields.BooleanField', [], {})
        },
        u'ratechecker.rate': {
            'Meta': {'object_name': 'Rate'},
            'base_rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'data_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'lock': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ratechecker.Product']"}),
            'rates_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['ratechecker.Region']", 'symmetrical': 'False'}),
            'total_points': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'})
        },
        u'ratechecker.region': {
            'Meta': {'object_name': 'Region'},
            'data_timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region_id': ('django.db.models.fields.IntegerField', [], {}),
            'state_id': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['ratechecker']