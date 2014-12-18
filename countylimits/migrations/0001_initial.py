# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'State'
        db.create_table(u'countylimits_state', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('state_fips', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('state_abbr', self.gf('localflavor.us.models.USStateField')(max_length=2)),
        ))
        db.send_create_signal(u'countylimits', ['State'])

        # Adding model 'County'
        db.create_table(u'countylimits_county', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('county_fips', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('county_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('state', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['countylimits.State'])),
        ))
        db.send_create_signal(u'countylimits', ['County'])

        # Adding model 'CountyLimit'
        db.create_table(u'countylimits_countylimit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fha_limit', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('gse_limit', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('va_limit', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=2)),
            ('county', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['countylimits.County'], unique=True)),
        ))
        db.send_create_signal(u'countylimits', ['CountyLimit'])


    def backwards(self, orm):
        # Deleting model 'State'
        db.delete_table(u'countylimits_state')

        # Deleting model 'County'
        db.delete_table(u'countylimits_county')

        # Deleting model 'CountyLimit'
        db.delete_table(u'countylimits_countylimit')


    models = {
        u'countylimits.county': {
            'Meta': {'object_name': 'County'},
            'county_fips': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'county_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['countylimits.State']"})
        },
        u'countylimits.countylimit': {
            'Meta': {'object_name': 'CountyLimit'},
            'county': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['countylimits.County']", 'unique': 'True'}),
            'fha_limit': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            'gse_limit': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'va_limit': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '2'})
        },
        u'countylimits.state': {
            'Meta': {'object_name': 'State'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'state_abbr': ('localflavor.us.models.USStateField', [], {'max_length': '2'}),
            'state_fips': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['countylimits']