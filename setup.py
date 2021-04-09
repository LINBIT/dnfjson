#!/usr/bin/env python

import setuptools

setuptools.setup(
    name="dnfjson",
    version="0.1.0",
    author="Christoph Böhmwalder",
    author_email="christoph.boehmwalder@linbit.com",
    description="A libdnf wrapper which produces machine readable output",
    url="https://github.com/chrboe/dnfjson",
    scripts=["dnfjson.py"],
    python_requires=">=3.6",
)
