#!/usr/bin/env python

import sys

from setuptools import setup, find_packages


dependencies = ['MediaCore >= 0.9.9dev']
if sys.version_info < (2, 7):
    dependencies.append('argparse')
# + MediaCore dependencies
#    - babel
#    - simplejson (Python < 2.6)

setup(
    name='MCYouTubeImport',
    version='0.6',
    
    author='Felix Schwarz',
    author_email='info@schwarz.eu',
    license='GPL v3 or later', # see LICENSE.txt
    
    packages=find_packages(),
    namespace_packages = ['mcore'],
    include_package_data=True,
    
    install_requires=dependencies, 
    entry_points = {
        'mediacore.plugin': [
            'youtube_import = mcore.youtube_import.mediacore_plugin',
        ],
        'console_scripts': [
            'import-youtube-videos = mcore.youtube_import.cli:import_command',
        ]
    },
    message_extractors = {'mcore/youtube_import': [
        ('**.py', 'python', None),
        ('templates/**.html', 'genshi', {'template_class': 'genshi.template.markup:MarkupTemplate'}),
    ]},
)

