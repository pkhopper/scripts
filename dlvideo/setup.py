#!/usr/bin/env python
# coding = utf-8

from setuptools import setup, find_packages

PACKAGE = "vavava"
NAME = "vavava"
DESCRIPTION = "tools"
AUTHOR = "vavava"
AUTHOR_EMAIL = "pk13610@gmail.com"
URL = "http://www.github.com/pkhopper"
VERSION = __import__(PACKAGE).__version__

setup(
    name = NAME,
    version = VERSION,
    description = DESCRIPTION,
    long_description = open("README.rst").read(),
    author = AUTHOR,
    author_email = AUTHOR_EMAIL,
    license = "BSD",
    url = URL,
    packages = find_packages(exclude = ["test.*", "test"]),
    # package_data = [],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ],
    zip_safe = False,
    # requires = []
)
