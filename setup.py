from setuptools import setup, find_packages

setup(name='MIDIUtil',
      version='1.0.1',
      description='A pure python library for creating multi-track MIDI files',
      author='Mark Conway Wirt',
      author_email='markcwirt) at (gmail . com',
      license='MIT',
      url='https://github.com/MarkCWirt/MIDIUtil',
      packages=find_packages(where="src"),
      package_dir = {'': 'src'},
      package_data={
          '' : ['License.txt', 'README.rst', 'documentation/*'],
          'examples' : ['single-note-example.py']},
      include_package_data = True,
      platforms='Platform Independent',
      classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'License :: OSI Approved :: MIT License',
          ],
      keywords = 'Music MIDI',
      long_description='''
This package provides a simple interface to allow Python programs to write multi-track MIDI files.'''
     )
