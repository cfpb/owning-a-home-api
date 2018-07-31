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
    'beautifulsoup4==4.5.3',
    'Django>=1.8,<1.12',
    'django-cors-headers',
    'dj-database-url==0.4.2',
    'django-localflavor',
    'djangorestframework==3.6.4', # Latest version that supports both Django 1.8 and 1.11
    'requests>2.18,<2.20',
    'unicodecsv==0.14.1',
]

testing_extras = [
    'coverage==4.2',
    'mock==2.0.0',
    'model_mommy==1.2.6',
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
        'testing': testing_extras,
    }
)
