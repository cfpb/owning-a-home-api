from datetime import date
from io import BytesIO
from zipfile import ZipFile

from ratechecker.dataset import Dataset


def get_sample_cover_sheet(day=None):
    day = day or date.today()

    return (
        "<data>"
        "<ProcessDate><Date>{day}</Date></ProcessDate>"
        "<Scenarios>"
        "<Scenario>"
        "<ScenarioNo>0</ScenarioNo>"
        "<AdjustedRates>3.25</AdjustedRates>"
        "<AdjustedPoints>1.75</AdjustedPoints>"
        "</Scenario>"
        "</Scenarios>"
        "</data>"
    ).format(day=day.strftime("%Y%m%d"))


def get_sample_dataset_zipfile(day=None, datasets=None):
    if datasets is None:
        datasets = {}
    day = day or date.today()

    f = BytesIO()
    zf = ZipFile(f, "w")
    zf.writestr("CoverSheet.xml", get_sample_cover_sheet(day=day))

    if not datasets:
        datestr = day.strftime("%Y%m%d")
        datasets = {
            "{}_{}.txt".format(datestr, k): "dummy"
            for k in Dataset.loaders.keys()  # noqa
        }

    for filename, contents in datasets.items():
        zf.writestr(filename, contents)

    zf.close()

    f.seek(0)
    return f


def write_sample_dataset(filename):
    content = get_sample_dataset_zipfile().read()
    with open(filename, "wb") as f:
        f.write(content)


def get_sample_dataset(day=None, datasets=None):
    if datasets is None:
        datasets = {}
    return Dataset(get_sample_dataset_zipfile(day=day, datasets=datasets))
