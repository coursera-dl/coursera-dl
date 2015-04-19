from setuptools import setup

# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too


setup(
    name='coursera',
    version='0.0.0',
    maintainer='Rogério Theodoro de Brito',
    maintainer_email='rbrito@ime.usp.br',

    license='LGPL',
    url='https://github.com/coursera-dl/coursera',

    install_requires=open('requirements.txt').readlines(),
    extras_require=dict(
        dev=open('requirements-dev.txt').readlines()
    ),

    description='Script for downloading Coursera.org videos and naming them.',
    long_description=open('README.md', 'r').read(),
    keywords=['python', 'FIXME'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python',
        'Topic :: Education',
        'Operating System :: OS Independent'
    ],

    packages=["coursera"],
    entry_points=dict(
        console_scripts=[
            'coursera-dl=coursera.coursera_dl:main'
        ]
    ),
)
