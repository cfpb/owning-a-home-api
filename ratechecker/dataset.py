import io
from collections import OrderedDict
from datetime import datetime, time
from xml.etree import cElementTree as ET
from zipfile import ZipFile

from django.utils import timezone
from django.utils.functional import cached_property

from ratechecker.loader import (
    AdjustmentLoader,
    ProductLoader,
    RateLoader,
    RegionLoader,
)


class Dataset(object):
    loaders = {
        "adjustment": AdjustmentLoader,
        "product": ProductLoader,
        "rate": RateLoader,
        "region": RegionLoader,
    }

    def __init__(self, f):
        self.zf = ZipFile(f)

    @cached_property
    def cover_sheet(self):
        with self.zf.open("CoverSheet.xml") as f:
            return CoverSheet(f)

    @cached_property
    def timestamp(self):
        ts = datetime.combine(self.cover_sheet.date, time.min)
        return timezone.make_aware(ts, timezone.get_current_timezone())

    @cached_property
    def filename_prefix(self):
        return self.cover_sheet.date.strftime("%Y%m%d")

    def load(self):
        # Sort the list of loaders so that Region loads last, as a bellwether
        for key, loader_cls in sorted(self.loaders.items()):
            try:
                f = self.datafile(key)
            except KeyError:
                # The fees data is expected to be temporarily unavailable,
                # so if the fees file is not found, we skip it and
                # continue loading the other data types.
                if key == "fee":
                    continue
                raise

            # The zip file may be opened as binary, but we want to process the
            # files that it contains as text.
            f_text = io.TextIOWrapper(f)
            loader = loader_cls(f_text, data_timestamp=self.timestamp)
            loader.load()

    def datafile(self, name):
        filename = "{}_{}.txt".format(self.filename_prefix, name)
        return self.zf.open(filename)


class CoverSheet(object):
    def __init__(self, f):
        self.tree = ET.parse(f)

        if not self.date:
            raise ValueError("missing date")

        if not self.expected_scenario_results:
            raise ValueError("missing scenario results")

    @property
    def date(self):
        node = self.tree.find("ProcessDate/Date")

        if node is not None:
            return datetime.strptime(node.text, "%Y%m%d").date()

    @property
    def expected_scenario_results(self):
        results = OrderedDict()

        for scenario in self.tree.iter(tag="Scenario"):
            scenario_data = {elem.tag: elem.text for elem in scenario}
            scenario_id = int(scenario_data["ScenarioNo"])

            results[scenario_id] = (
                scenario_data["AdjustedRates"] or None,
                scenario_data["AdjustedPoints"] or None,
            )

        return results
