Please, before sending patches, it is helpful if you:

* Make sure that you have all dependencies installed, like via

        pip install -r requirements

* Run the test suite with

        nosetests --verbose --with-coverage --cover-package=coursera

* Check for any potential bugs with the help of [`pep8`][pep8],
  [`pyflakes`][pyflakes], and [`pylint`][pylint].

[pep8]: https://pypi.python.org/pypi/pep8
[pyflakes]: https://pypi.python.org/pypi/pyflakes/
[pylint]: https://pypi.python.org/pypi/pylint

If you happen to find any issue reported by these programs, we would welcome
you to fix them, as they are usually very easy to fix and we would all
benefit from a better code base.
