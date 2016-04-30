#!/usr/bin/env python

import os
from distutils.core import setup
from setuptools import find_packages


def long_desc(root_path):
    FILES = ['README.md']
    for filename in FILES:
        filepath = os.path.realpath(os.path.join(root_path, filename))
        if os.path.isfile(filepath):
            with open(filepath, mode='r') as f:
                yield f.read()


HERE = os.path.abspath(os.path.dirname(__file__))
long_description = "\n\n".join(long_desc(HERE))


def get_version(root_path):
    with open(os.path.join(root_path, 'scheduler', '__init__.py')) as f:
        for line in f:
            if line.startswith('__version__ ='):
                return line.split('=')[1].strip().strip('"\'')


tests_require = [
    'factory_boy>=2.6.1',
    'psycopg2>=2.6.1',
]


setup(
    name='django-rq-scheduler',
    version=get_version(HERE),
    description='A database backed job scheduler for Django RQ',
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    author='Chad Shryock',
    author_email='chad@isl.co',
    url='https://github.com/istrategylabs/django-rq-scheduler',
    zip_safe=True,
    install_requires=[
        'django>=1.9.0',
        'django-model-utils>=2.4.0',
        'django-rq>=0.9.0',
        'rq_scheduler>=0.5.1',
        'pytz>=2015.7',
    ],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
    ],
)
