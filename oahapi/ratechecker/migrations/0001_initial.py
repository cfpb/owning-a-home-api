# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Product'
        db.create_table(u'ratechecker_product', (
            ('plan_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('institution', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('loan_purpose', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('pmt_type', self.gf('django.db.models.fields.CharField')(default='FIXED', max_length=12)),
            ('loan_type', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('loan_term', self.gf('django.db.models.fields.IntegerField')()),
            ('int_adj_term', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('adj_period', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('io', self.gf('django.db.models.fields.BooleanField')()),
            ('arm_index', self.gf('django.db.models.fields.CharField')(max_length=96, null=True)),
            ('int_adj_cap', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('annual_cap', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('loan_cap', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('arm_margin', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4)),
            ('ai_value', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=4)),
            ('min_ltv', self.gf('django.db.models.fields.FloatField')()),
            ('max_ltv', self.gf('django.db.models.fields.FloatField')()),
            ('min_fico', self.gf('django.db.models.fields.IntegerField')()),
            ('max_fico', self.gf('django.db.models.fields.IntegerField')()),
            ('min_loan_amt', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('max_loan_amt', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('singlefamily', self.gf('django.db.models.fields.BooleanField')()),
            ('condo', self.gf('django.db.models.fields.BooleanField')()),
            ('coop', self.gf('django.db.models.fields.BooleanField')()),
        ))
        db.send_create_signal(u'ratechecker', ['Product'])

        # Adding model 'Adjustment'
        db.create_table(u'ratechecker_adjustment', (
            ('rule_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ratechecker.Product'])),
            ('affect_rate_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('adj_value', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=6, decimal_places=3)),
            ('min_loan_amt', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=2)),
            ('max_loan_amt', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=2)),
            ('prop_type', self.gf('django.db.models.fields.CharField')(max_length=10, null=True)),
            ('min_fico', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('max_fico', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('min_ltv', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('max_ltv', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=2, null=True)),
        ))
        db.send_create_signal(u'ratechecker', ['Adjustment'])

        # Adding model 'Region'
        db.create_table(u'ratechecker_region', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('region_id', self.gf('django.db.models.fields.IntegerField')()),
            ('state_id', self.gf('django.db.models.fields.CharField')(max_length=2)),
        ))
        db.send_create_signal(u'ratechecker', ['Region'])

        # Adding model 'Rate'
        db.create_table(u'ratechecker_rate', (
            ('rates_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ratechecker.Product'])),
            ('lock', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('base_rate', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=3)),
            ('total_points', self.gf('django.db.models.fields.DecimalField')(max_digits=6, decimal_places=3)),
        ))
        db.send_create_signal(u'ratechecker', ['Rate'])

        # Adding M2M table for field regions on 'Rate'
        m2m_table_name = db.shorten_name(u'ratechecker_rate_regions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('rate', models.ForeignKey(orm[u'ratechecker.rate'], null=False)),
            ('region', models.ForeignKey(orm[u'ratechecker.region'], null=False))
        ))
        db.create_unique(m2m_table_name, ['rate_id', 'region_id'])


    def backwards(self, orm):
        # Deleting model 'Product'
        db.delete_table(u'ratechecker_product')

        # Deleting model 'Adjustment'
        db.delete_table(u'ratechecker_adjustment')

        # Deleting model 'Region'
        db.delete_table(u'ratechecker_region')

        # Deleting model 'Rate'
        db.delete_table(u'ratechecker_rate')

        # Removing M2M table for field regions on 'Rate'
        db.delete_table(db.shorten_name(u'ratechecker_rate_regions'))


    models = {
        u'ratechecker.adjustment': {
            'Meta': {'object_name': 'Adjustment'},
            'adj_value': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '3'}),
            'affect_rate_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
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
            'singlefamily': ('django.db.models.fields.BooleanField', [], {})
        },
        u'ratechecker.rate': {
            'Meta': {'object_name': 'Rate'},
            'base_rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'}),
            'lock': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ratechecker.Product']"}),
            'rates_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['ratechecker.Region']", 'symmetrical': 'False'}),
            'total_points': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '3'})
        },
        u'ratechecker.region': {
            'Meta': {'object_name': 'Region'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region_id': ('django.db.models.fields.IntegerField', [], {}),
            'state_id': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['ratechecker']