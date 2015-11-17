# -*- coding: utf-8 -*-

# This file is part of CartoDB Backup.
# https://github.com/GeographicaGS/CartoDB_Backup

# Licensed under the GPLv2 license:
# https://www.gnu.org/licenses/gpl-2.0.txt
# Copyright (c) 2015, Cayetano Benavent <cayetano.benavent@geographica.gs>

from setuptools import setup, find_packages


# Get the long description from README file.
# Before upload a new version run rstgenerator.sh
# to update Readme reStructuredText file from
# original Readme markdown file.
with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='cartodb_backup',
    version='0.1',

    description='Python CLI to make a backup of an entire CartoDB domain to SQL dump file (zipped). Optionally you can restore SQL dumped file to a new (created) PostGIS DB. Also you can upload sql files to Amazon S3.',
    long_description=long_description,

    author='Cayetano Benavent',
    author_email='cayetano.benavent@geographica.gs',

    scripts=['bin/cartodb_backup'],

    # The project's main homepage.
    url='http://github.com/GeographicaGS/CartoDB_Backup',

    # Licensed under the GPLv2 license:
    # https://www.gnu.org/licenses/gpl-2.0.txt
    license='GPLv2',

    # According to: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: GIS'
    ],

    keywords='cartodb GIS postgis',

    packages=find_packages(),
    include_package_data=False,
    install_requires=[
        'psycopg2>=2.4.5,<3.0',
        'boto>=2.38.0,<3.0',

    ]

)
