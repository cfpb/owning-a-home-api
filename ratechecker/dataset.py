from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict
from datetime import datetime, time
from django.utils import timezone
from django.utils.functional import cached_property
import xml.etree.cElementTree as ET
from zipfile import ZipFile

from ratechecker.loader import (
    AdjustmentLoader, FeeLoader, ProductLoader, RateLoader, RegionLoader
)


class Dataset(object):
    loaders = {
        'adjustment': AdjustmentLoader,
        'fee': FeeLoader,
        'product': ProductLoader,
        'rate': RateLoader,
        'region': RegionLoader,
    }

    def __init__(self, f):
        self.zf = ZipFile(f)

    @cached_property
    def cover_sheet(self):
        with self.zf.open('CoverSheet.xml') as f:
            return CoverSheet(f)

    @cached_property
    def timestamp(self):
        ts = datetime.combine(self.cover_sheet.date, time.min)
        return timezone.make_aware(ts, timezone.get_current_timezone())

    @cached_property
    def filename_prefix(self):
        return self.cover_sheet.date.strftime('%Y%m%d')

    def load(self):
        for key, loader_cls in self.loaders.items():
            try:
                f = self.datafile(key)
            except KeyError:
                if key == 'fee':
                    continue
                raise
            except Exception:
                raise
            loader = loader_cls(f, data_timestamp=self.timestamp)
            loader.load()

    def datafile(self, name):
        filename = '{}_{}.txt'.format(self.filename_prefix, name)
        return self.zf.open(filename)


class CoverSheet(object):
    def __init__(self, f):
        self.tree = ET.parse(f)

        if not self.date:
            raise ValueError('missing date')

        if not self.expected_scenario_results:
            raise ValueError('missing scenario results')

    @property
    def date(self):
        node = self.tree.find('ProcessDate/Date')

        if node is not None:
            return datetime.strptime(node.text, '%Y%m%d').date()

    @property
    def expected_scenario_results(self):
        results = OrderedDict()

        for scenario in self.tree.getiterator(tag='Scenario'):
            scenario_data = {elem.tag: elem.text for elem in scenario}
            scenario_id = int(scenario_data['ScenarioNo'])

            results[scenario_id] = (
                scenario_data['AdjustedRates'] or None,
                scenario_data['AdjustedPoints'] or None
            )

        return results
