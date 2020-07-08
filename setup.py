import os
from setuptools import setup, find_packages


install_requires = [
    "beautifulsoup4>=4.5.0,<4.9",
    "Django>=1.11,<2.3",
    "django-cors-headers",
    "dj-database-url>=0.4.2,<1",
    "django-localflavor>=1.1,<3.1",
    "djangorestframework>=3.9.1,<4.0",
    "requests>=2.18,<3",
]

setup_requires = [
    "cfgov-setup==1.2",
    "setuptools-git-version==1.0.3",
]

testing_extras = [
    "coverage>=4.5.1,<5",
    "mock==2.0.0",
    "model_mommy>=1.6.0,<1.7",
]

docs_extras = [
    "mkdocs==0.17.5",
    "mkDOCter==1.0.5",
]


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ""


setup(
    name="owning-a-home-api",
    author="CFPB",
    author_email="tech@cfpb.gov",
    version_format="{tag}.dev{commitcount}+{gitsha}",
    maintainer="cfpb",
    maintainer_email="tech@cfpb.gov",
    packages=find_packages(),
    package_data={
        "countylimits": [
            "data/base_data/*.csv",
            "data/test/*.csv",
            "data_collection/*.txt",
            "fixtures/*.json",
        ],
    },
    include_package_data=True,
    description="Owning a home api",
    classifiers=[
        "Topic :: Internet :: WWW/HTTP",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Framework :: Django",
        "Development Status :: 5 - Production/Stable",
        "Operating System :: OS Independent",
    ],
    long_description=read_file("README.md"),
    zip_safe=False,
    python_requires=">=3",
    install_requires=install_requires,
    setup_requires=setup_requires,
    extras_require={"docs": docs_extras, "testing": testing_extras},
)
