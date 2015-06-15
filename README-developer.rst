Developer notes
===============

Setup
-----

Of course, you need python to be installed.

Then, make sure that ``pip`` is installed; if not, do

::

    easy_install pip

to install it. Next, install ``wheel``

::

    pip install wheel

Note: the steps listed above need only be done once.

Testing before packaging
------------------------

::

    PYTHONPATH=/Users/kelley/src/nota python -m nota

Packaging
---------

Each time the ``nota`` source is updated, do the following to test and package
it:

::

    python setup.py test
    python setup.py sdist
    python setup.py bdist_wheel --universal

After this, the ``dist`` directory will contain some packages.

Installing package locally
--------------------------

To install a local test version, do e.g. (with the up-to-date version number, if the line below has the wrong one)

::

    sudo -H pip install dist/nota-0.7.4.tar.gz --upgrade

Installing package on pypi.python
---------------------------------

To submit to ``pypi.python.org`` remove old versions from ``dist`` and
then do:

::

    twine upload dist/*

Suggested aliases for nota
--------------------------

The developer uses the following, so that ``n`` runs the packaged version and
``nn`` runs the new (source-code) version.

::

    alias n=nota
    alias nn='PYTHONPATH=~/src/nota python -m nota'

