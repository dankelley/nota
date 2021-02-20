import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(name='nota',
      version='0.8.9',
      description='Text-based note taker',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://github.com/dankelley/nota',
      author='Dan Kelley',
      author_email='kelley.dan@gmail.com',
      license='GPL3',
      packages=['nota'],
      python_requires='>=3.6',
      classifiers=['Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Topic :: Utilities',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'],
      test_suite="tests",
      entry_points={ 'console_scripts':
          [ 'nota = nota.main:nota' ]
          },
      zip_safe=True)
