#
# Fabric configuration - http://www.fabfile.org/
#

from __future__ import print_function

import errno
import os

from fabric.api import (env, local, task)

MD2RST='pandoc --from=markdown_github --to=rst --output=README.rst README.md'

if not os.path.exists('README.rst'):
    local(MD2RST)

env.projname = local("python setup.py --name", capture=True)
env.version = local("python setup.py --version", capture=True)


def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


@task
def create_rst_doc():
    local(MD2RST)


@task
def clean():
    create_rst_doc()
    local("python setup.py clean")
    local("rm -rf .tox coursera.egg-info htmlcov build dist README.rst")
    local("rm -rf coursera/__pycache__/ coursera/test/__pycache__/")
    local("find . -name '*.pyc' -delete")


@task
def build():
    create_rst_doc()
    local("python setup.py sdist")
    local("gpg --detach-sign -a dist/coursera-%s.tar.gz" % env.version)


@task
def rebuild():
    clean()
    build()


@task
def coverage():
    local("py.test coursera/test -v --cov coursera --cov-report html \
          --cov-report term-missing")


@task
def pylint():
    local("pylint %s tests" % env.projname)


@task
def tox():
    local('tox')


@task
def release_check():
    """Check if there is a Git tag already in place"""
    tags = local("git tag", capture=True)
    tags = set(tags.splitlines())
    if env.version in tags:
        raise Exception("Already released v. %r" % env.version)


@task
def release():
    """Release a new version"""
    release_check()
    build()
    print("Releasing %s version %s." % (env.projname, env.version))
    local("git tag %s" % env.version)
    local('twine upload dist/coursera-*.tar.gz*')
    local("git push")
    local("git push --tags")
