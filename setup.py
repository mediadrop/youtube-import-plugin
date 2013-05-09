#!/usr/bin/env python
# This file is a part of the YouTube Import plugin for MediaCore CE.
# The source code contained in this file is licensed under the GPL v3 (or at 
# your option any later version).
# See LICENSE.txt in the main project directory for more information.

import sys

from setuptools import setup, find_packages


dependencies = [
    'babel',
    'MediaCore >= 0.10.0b1',
    'simplejson',
]
if sys.version_info < (2, 7):
    dependencies.append('argparse')

setup(
    name='MCYouTubeImport',
    version='0.9',
    
    author='Felix Schwarz',
    author_email='info@schwarz.eu',
    license='GPL v3 or later', # see LICENSE.txt
    
    packages=find_packages(),
    namespace_packages = ['mediacoreext'],
    include_package_data=True,
    
    install_requires=dependencies, 
    entry_points = {
        'mediacore.plugin': [
            'youtube_import = mediacoreext.youtube_import.mediacore_plugin',
        ],
        'console_scripts': [
            'import-youtube-videos = mediacoreext.youtube_import.cli:import_command',
        ]
    },
    message_extractors = {'mediacoreext/youtube_import': [
        ('**.py', 'python', None),
        ('templates/**.html', 'genshi', {'template_class': 'genshi.template.markup:MarkupTemplate'}),
    ]},
)

