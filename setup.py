#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='MCYouTubeImport',
    version='0.6',
    
    author='Felix Schwarz',
    author_email='info@schwarz.eu',
    license='GPL v3 or later', # see LICENSE.txt
    
    packages=find_packages(),
    namespace_packages = ['mcore'],
    include_package_data=True,
    entry_points = {
        'mediacore.plugin': [
            'youtube_import = mcore.youtube_import.mediacore_plugin',
        ],
    },
    message_extractors = {'mcore/youtube_import': [
        ('**.py', 'python', None),
        ('templates/**.html', 'genshi', {'template_class': 'genshi.template.markup:MarkupTemplate'}),
    ]},
)

