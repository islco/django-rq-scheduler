#!/usr/bin/env python

import os
from distutils.core import setup

from setuptools import find_packages


def long_desc(root_path):
    FILES = ["README.md"]
    for filename in FILES:
        filepath = os.path.realpath(os.path.join(root_path, filename))
        if os.path.isfile(filepath):
            with open(filepath, mode="r") as f:
                yield f.read()


PATH_OF_RUNNING_SCRIPT = os.path.abspath(os.path.dirname(__file__))
long_description = "\n\n".join(long_desc(PATH_OF_RUNNING_SCRIPT))


def get_version(root_path):
    with open(os.path.join(root_path, "scheduler", "__init__.py")) as f:
        for line in f:
            if line.startswith("__version__ ="):
                return line.split("=")[1].strip().strip("\"'")


tests_require = [
    'factory_boy>=2.11.1',
]


setup(
    name="django-rq-scheduler",
    version=get_version(PATH_OF_RUNNING_SCRIPT),
    description="A database backed job scheduler for Django RQ",
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    author="Chad Shryock",
    author_email="chad@keystone.works",
    url="https://github.com/isl-x/django-rq-scheduler",
    zip_safe=True,
    install_requires=[
        "django>=2.0",
        "django-model-utils>=2.4.0",
        "django-rq>=0.9.3",
        "rq-scheduler>=0.6.0",
        "pytz>=2018.5",
        "croniter>=0.3.24",
    ],
    tests_require=tests_require,
    test_suite='scheduler.tests',
    extras_require={
        "test": tests_require,
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Framework :: Django",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 3.0",
    ],
)
