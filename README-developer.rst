Developer notes
===============

References
----------

1. https://packaging.python.org/tutorials/packaging-projects/ provides information on packaging.

Setup
-----

Of course, you need python3 to be installed.

Then, make sure that ``pip`` is installed; if not, do

::

    easy_install-3.8 pip

to install it. Next, install ``wheel``

::

    pip3.8 install wheel

Note: the steps listed above need only be done once.

Increasing the version number
-----------------------------

Several manual steps are required.

1. Alter the 'version=' line in `setup.py`.
2. Ensure that `README.md` has an entry for the version.
3. Ensure that the version numbers in the present document are updated, so that
   cut/paste will work for local installations.
4. Update the `self.appversion =` line in `nota/notaclass.py` for the new version. Look
   carefully at the nearby code, if changes have been made to the database.
5. Remove old files from the `dist/` directory.
6. Perform the steps listed under "Packaging" and "Installing package locally" below.
7. Use it for a while, only updating to pypi (see "Installing package on pypi.python" below)
   when it is clear that this new version is good.

Testing before packaging
------------------------


::

    PYTHONPATH=/Users/kelley/git/nota python3 -m nota

Packaging
---------

Each time the ``nota`` source is updated, do the following to test and package
it:

::

    python3 setup.py test
    python3 setup.py sdist
    python3 setup.py bdist_wheel --universal

After this, the ``dist`` directory will contain some packages.

Installing package locally
--------------------------

To install a local test version, do e.g. (with the up-to-date version number, if the line below has the wrong one)

::

    sudo -H pip3 install dist/nota-0.8.10.tar.gz --upgrade


Installing package on pypi.python
---------------------------------

To submit to ``pypi.python.org`` remove old versions from ``dist`` and
then do:

::

    pip3.9 install twine
    twine upload dist/*


**Reminder** After uploading, be sure to increment the version number (a) in
line 4 of setup.py, (b) in the present file and (c) in nota/notaclass.py where
self.appversion is define. Then add a blank entry for this new version, in
README.rst.


Suggested aliases for nota
--------------------------

The developer uses the following, so that ``n`` runs the packaged version and
``nn`` runs the new (source-code) version.

::

    alias n=nota
    alias nn='PYTHONPATH=~/git/nota python3 -m nota'

