import os
from setuptools import setup


setup(
    name='coursera-dl',
    description="Script for downloading Coursera.org videos and naming them.",
    version='0.1.0',
    author="John Lehmann",
    author_email="JohnLehmann@gmail.com",
    url='https://github.com/coursera-dl/coursera',
    packages=['coursera'],
    install_requires = [
        'beautifulsoup4',
        'html5lib',
        'requests',
        'six',
    ],
    entry_points = {
        'console_scripts': [ 'coursera-dl=coursera.coursera_dl:main' ],
    },
)
