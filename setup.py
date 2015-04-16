from setuptools import setup

# you can install this to a local test virtualenv like so:
#   virtualenv venv
#   ./venv/bin/pip install --editable .
#   ./venv/bin/pip install --editable .[dev]  # with dev requirements, too


setup(
    name='coursera',
    version='0.0.0',  # FIXME
    author='fixme',
    author_email='fixme',
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
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        # XXX FIXME add more, these are "Trove Classifiers"
    ],

    packages=["coursera"],
    entry_points=dict(
        console_scripts=[
            'coursera-dl=coursera.coursera_dl:main'
        ]
    ),
)
