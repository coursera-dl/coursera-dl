"""
Helper functions that are only used in tests.
"""
import os


def slurp_fixture(path):
    return open(os.path.join(os.path.dirname(__file__),
                             "fixtures", path), encoding='utf8').read()
