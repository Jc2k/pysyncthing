#!/usr/bin/python
# Copyright 2014 John Carr
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from distutils.core import setup


setup(
    name='pysyncthing',
    version='0.0.0dev0',
    description='Syncthing local "mist" syncing',
    license='LGPL-2.1+',
    url='https://github.com/Jc2k/pysyncthing',
    author='John Carr',
    author_email='john.carr@unrouted.co.uk',
    packages=[
        'pysyncthing',
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
