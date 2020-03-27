import csv
import itertools
from decimal import Decimal

from django.utils import timezone

from ratechecker.models import Adjustment, Product, Rate, Region


class LoaderError(BaseException):
    pass


def split(iterable, chunk_size=1000):
    sourceiter = iter(iterable)
    while True:
        chunk = list(itertools.islice(sourceiter, chunk_size))
        if not chunk:
            return

        yield chunk


class Loader(object):
    model_cls = None

    def __init__(self, f, delimiter="\t", data_timestamp=None):
        self.f = f
        self.delimiter = delimiter
        self.data_timestamp = data_timestamp or timezone.now()
        self.count = 0

    def load(self):
        instance_generator = self.generate_instances()
        for chunk in split(instance_generator):
            self.model_cls.objects.bulk_create(chunk)

        if 0 == self.count:
            raise LoaderError("no instances loaded")

    def generate_instances(self):
        entries = set()
        reader = csv.DictReader(self.f, delimiter=str(self.delimiter))

        for row in reader:
            if "ratesid" in row:
                if row["ratesid"] not in entries:
                    yield self.make_instance(row)
                    entries.add(row["ratesid"])
                    self.count += 1
            else:
                yield self.make_instance(row)
                self.count += 1

    def make_instance(self, row):
        raise NotImplementedError("implemented in derived classes")

    @staticmethod
    def nullable_int(row_item):
        if row_item.strip():
            try:
                return int(row_item)
            except ValueError:
                return int(float(row_item))

    @staticmethod
    def nullable_string(row_item):
        if row_item.strip():
            return row_item.strip()

    @staticmethod
    def nullable_decimal(row_item):
        if row_item.strip():
            return Decimal(row_item.strip()).quantize(Decimal(".001"))

    @staticmethod
    def string_to_boolean(bstr):
        if bstr.lower() == "true" or bstr == "1":
            return True
        elif bstr.lower() == "false" or bstr == "0":
            return False


class AdjustmentLoader(Loader):
    model_cls = Adjustment

    def make_instance(self, row):
        adj_value = self.nullable_decimal(row["adjvalue"])

        return self.model_cls(
            product_id=int(row["planid"]),
            rule_id=int(row["ruleid"]),
            affect_rate_type=row["affectratetype"],
            adj_value=adj_value if adj_value is not None else 0,
            min_loan_amt=self.nullable_decimal(row["minloanamt"]),
            max_loan_amt=self.nullable_decimal(row["maxloanamt"].strip()),
            prop_type=self.nullable_string(row["proptype"]),
            min_fico=self.nullable_int(row["minfico"]),
            max_fico=self.nullable_int(row["maxfico"]),
            min_ltv=self.nullable_decimal(row["minltv"]),
            max_ltv=self.nullable_decimal(row["maxltv"]),
            state=row["state"],
            data_timestamp=self.data_timestamp,
        )


class ProductLoader(Loader):
    model_cls = Product

    def make_instance(self, row):
        return self.model_cls(
            plan_id=int(row["planid"]),
            institution=row["institution"],
            loan_purpose=row["loanpurpose"],
            pmt_type=row["pmttype"],
            loan_type=row["loantype"],
            loan_term=int(row["loanterm"]),
            int_adj_term=self.nullable_int(row["intadjterm"]),
            adj_period=self.nullable_int(row["adjperiod"]),
            io=self.string_to_boolean(row["i/o"]),
            arm_index=self.nullable_string(row["armindex"]),
            int_adj_cap=self.nullable_int(row["initialadjcap"]),
            annual_cap=self.nullable_int(row["annualcap"]),
            loan_cap=self.nullable_int(row["loancap"]),
            arm_margin=self.nullable_decimal(row["armmargin"]),
            ai_value=self.nullable_decimal(row["aivalue"]),
            min_ltv=Decimal(row["minltv"]).quantize(Decimal(".001")),
            max_ltv=Decimal(row["maxltv"]).quantize(Decimal(".001")),
            min_fico=int(row["minfico"]),
            max_fico=int(row["maxfico"]),
            min_loan_amt=Decimal(row["minloanamt"]),
            max_loan_amt=Decimal(row["maxloanamt"]),
            data_timestamp=self.data_timestamp,
        )


class RateLoader(Loader):
    model_cls = Rate

    def make_instance(self, row):
        return self.model_cls(
            rate_id=int(row["ratesid"]),
            product_id=int(row["planid"]),
            region_id=int(row["regionid"]),
            lock=int(row["lock"]),
            base_rate=Decimal(row["baserate"]),
            total_points=Decimal(row["totalpoints"]),
            data_timestamp=self.data_timestamp,
        )


class RegionLoader(Loader):
    model_cls = Region

    def make_instance(self, row):
        return self.model_cls(
            region_id=int(row["RegionID"]),
            state_id=row["StateID"],
            data_timestamp=self.data_timestamp,
        )
