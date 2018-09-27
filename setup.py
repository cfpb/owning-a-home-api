import os
from setuptools import setup, find_packages


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


install_requires = [
    'beautifulsoup4>=4.5.0,<4.7',
    'Django>=1.11,<1.12',
    'django-cors-headers',
    'dj-database-url>=0.4.2,<1',
    'django-localflavor',
    'djangorestframework>=3.6,<3.9',
    'requests>=2.18,<3',
    'unicodecsv==0.14.1',
]

testing_extras = [
    'coverage>=4.5.1,<5',
    'mock==2.0.0',
    'model_mommy>=1.6.0,<1.7',
]

docs_extras = [
    'mkdocs==0.17.5',
    'mkDOCter==1.0.5',
]


setup(
    name='owning-a-home-api',
    version_format='{tag}.dev{commitcount}+{gitsha}',
    author='CFPB',
    author_email='tech@cfpb.gov',
    packages=find_packages(),
    package_data={
        'countylimits': [
            'data/base_data/*.csv',
            'data/test/*.csv',
            'data_collection/*.txt',
            'fixtures/*.json',
        ],
    },
    include_package_data=True,
    description=u'Owning a home api',
    classifiers=[
        'Topic :: Internet :: WWW/HTTP',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
        'Development Status :: 5 - Production/Stable',
        'Operating System :: OS Independent',
    ],
    setup_requires=['setuptools-git-version==1.0.3'],
    long_description=read_file('README.md'),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'docs': docs_extras,
        'testing': testing_extras,
    }
)
