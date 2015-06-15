from setuptools import setup

setup(name='nota',
      version='0.7.4',
      description='Text-based note taker',
      url='https://github.com/dankelley/nota',
      author='Dan Kelley',
      author_email='kelley.dan@gmail.com',
      license='GPL3',
      packages=['nota'],
      classifiers=['Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Topic :: Utilities',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'],
      test_suite="tests",
      entry_points={ 'console_scripts':
          [ 'nota = nota.main:nota' ]
          },
      zip_safe=True)
