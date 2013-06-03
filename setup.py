#!/usr/bin/env python
import os
from setuptools import setup

setup(
    name = "Trip",
    version = "0.0.1",
    author = "Jesse Vander Does",
    scripts = ["bin/run-trip-server.py"],
    package_dir = {'':'src'},
    packages=['Journey'],
    install_requires=["numpy","scipy","geolocator","bottle"],
)

