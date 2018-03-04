from setuptools import setup, find_packages


with open('README.rst') as file:
    long_description = file.read()

setup(name='MIDIUtil',
      version='1.2.1',
      description='A pure python library for creating multi-track MIDI files',
      author='Mark Conway Wirt',
      author_email='MarkCWirt@gmail.com',
      license='MIT',
      url='https://github.com/MarkCWirt/MIDIUtil',
      packages=find_packages(where="src"),
      package_dir = {'': 'src'},
      package_data={
          '' : ['License.txt', 'README.rst', 'documentation/*'],
          'examples' : ['single-note-example.py', 'c-major-scale.py']},
      include_package_data = True,
      platforms='Platform Independent',
      classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Topic :: Multimedia :: Sound/Audio :: MIDI',
          ],
      keywords = 'Music MIDI',
      long_description=long_description
     )
