MIDIUtil
========

|build|

This is just a brief adumbration. Full documentation for the release
version can be found at `Read the Docs
<http://midiutil.readthedocs.io/>`_. The documentation for the
development version is `here <http://midiutil.readthedocs.io/en/latest/>`_.

|docs|

Introduction
------------

MIDIUtil is a pure Python library that allows one to write multi-track
Musical Instrument Digital Interface (MIDI) files from within Python
programs (both format 1 and format 2 files are now supported).
It is object-oriented and allows one to create and write these
files with a minimum of fuss.

MIDIUtil isn't a full implementation of the MIDI specification. The actual
specification is a large, sprawling document which has organically grown
over the course of decades. I have selectively implemented some of the
more useful and common aspects of the specification. The choices have
been somewhat idiosyncratic; I largely implemented what I needed. When
I decided that it could be of use to other people I fleshed it out a bit,
but there are still things missing. Regardless, the code is fairly easy to
understand and well structured. Additions can be made to the library by
anyone with a good working knowledge of the MIDI file format and a good,
working knowledge of Python. Documentation for extending the library
is provided.

This software was originally developed with Python 2.5.2 and made use of
some features that were introduced in 2.5. More recently Python 2 and 3
support has been unified, so the code should work in both environments.
However, support for versions of Python previous to 2.7 has been dropped.
Any mission-critical music generation systems should probably be updated
to a version of Python supported and maintained by the Python foundation,
lest society devolve into lawlessness.

This software is distributed under an Open Source license and you are
free to use it as you see fit, provided that attribution is maintained.
See License.txt in the source distribution for details.

Installation
------------

The latest, stable version of MIDIUtil is hosted at the `Python Package
Index <https://pypi.python.org/pypi/MIDIUtil/>`__ and can be installed
via the normal channels:

.. code:: bash

  pip install MIDIUtil

Source code is available on `Github <https://github.com/MarkCWirt/MIDIUtil>`__ ,
and be cloned with one of the following URLS:

.. code:: bash

    git clone git@github.com:MarkCWirt/MIDIUtil.git
    # or
    git clone https://github.com/MarkCWirt/MIDIUtil.git

depending on if you want to use SSH or HTTPS. (The source code
for stable releases can also be downloaded from the
`Releases <https://github.com/MarkCWirt/MIDIUtil/releases>`__
page.)

To use the library one can either install it on one's system:

.. code:: bash

    python setup.py install

or point your ``$PYTHONPATH`` environment variable to the directory
containing ``midiutil`` (i.e., ``src``).

MIDIUtil is pure Python and should work on any platform to which
Python has been ported.

If you're using this software in your own projects
you may want to consider distributing the library bundled with yours;
the library is small and self-contained, and such bundling makes things
more convenient for your users. The best way of doing this is probably
to copy the midiutil directory directly to your package directory and
then refer to it with a fully qualified name. This will prevent it from
conflicting with any version of the software that may be installed on
the target system.


Quick Start
-----------

Using the software is easy:

* The package must be imported into your namespace
* A MIDIFile object is created
* Events (notes, tempo-changes, etc.) are added to the object
* The MIDI file is written to disk.

Detailed documentation is provided; what follows is a simple example
to get you going quickly. In this example we'll create a one track MIDI
File, assign a tempo to the track, and write a C-Major scale. Then we
write it to disk.

.. code:: python

    #!/usr/bin/env python

    from midiutil import MIDIFile

    degrees  = [60, 62, 64, 65, 67, 69, 71, 72]  # MIDI note number
    track    = 0
    channel  = 0
    time     = 0    # In beats
    duration = 1    # In beats
    tempo    = 60   # In BPM
    volume   = 100  # 0-127, as per the MIDI standard

    MyMIDI = MIDIFile(1)  # One track, defaults to format 1 (tempo track is created
                          # automatically)
    MyMIDI.addTempo(track, time, tempo)

    for i, pitch in enumerate(degrees):
        MyMIDI.addNote(track, channel, pitch, time + i, duration, volume)

    with open("major-scale.mid", "wb") as output_file:
        MyMIDI.writeFile(output_file)

There are several additional event types that can be added and there are
various options available for creating the MIDIFile object, but the above
is sufficient to begin using the library and creating note sequences.

The above code is found in machine-readable form in the examples directory.
A detailed class reference and documentation describing how to extend
the library is provided in the documentation directory.

Have fun!

Thank You
---------

I'd like to mention the following people who have given feedback, bug
fixes,  and suggestions on the library:

* Bram de Jong
* Mike Reeves-McMillan
* Egg Syntax
* Nils Gey
* Francis G.
* cclauss (Code formating cleanup and PEP-8 stuff, which I'm not good at following).
* Philippe-Adrien Nousse (Adphi) for the pitch bend implementation.
* meteorsw (https://github.com/meteorsw) for major restructuring and clean-up
  of code.

I've actually been off email for a few years, so I'm sure there are lots
of suggestions waiting. Stay tuned for updates and bug fixes!

.. |docs| image:: https://readthedocs.org/projects/midiutil/badge/?version=1.1.3
   :target: http://midiutil.readthedocs.io/
   :alt: Documentation Status

.. |build| image:: https://travis-ci.org/MarkCWirt/MIDIUtil.svg?branch=master
   :target: https://travis-ci.org/MarkCWirt/MIDIUtil
