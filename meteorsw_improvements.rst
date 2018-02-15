========================
Improvements to MIDIUtil
========================

:date: 2018-02-14

Abstract
========
I decided to use this library in a project I was working on.  As I read the
code, I saw some things that should be improved.  This document is where I
will write down my thoughts and describe the changes I have made.


GenericEvent class is crazy
===========================
The first obvious mess is the GenericEvent class, which is intended to be a
base class, but has a method ``__eq__()`` that knows specifics about derived
derived classes.  The author himself realizes this is horrible, as evidenced
by a comment he wrote.

Fixing this is rather easy, but I first will make a couple of other smaller
improvements, and then come back to this flaw.


GenericEvent class ``type`` attribute
=====================================
GenericEvent has a ``type`` attribute which holds a name of the type
of the derived class. This attribute is used in the aforementioned
``__eq__()`` method, and in three other places in the code which work on
a list which may contain instances of various subclasses of GenericEvent.

So this ``type`` parameter is only used to allow some outside code to determine
which kind of subclass of GenericEvent it is operating on.

There is no reason it needs to be an instance attribute. It can be
a class attribute.  This will simplify the constructor signature of
GenericEvent.

I also think that ``type`` is not a good name for this attribute, since
``type`` is also the name of a built-in function in Python. So I will change
it to ``evtname``.


.. Note: The way the source tree is organized, you can't run the unit tests
   without installing the midiutil package. To work around this inconvenience
   I run the unit tests with a ``PYTHONPATH`` environment variable so that
   ``test_midi.py`` can successfully import ``midiutil.MidiFile``.

   Like this::

     MIDIUtil/src$ PYTHONPATH=`pwd` unittests/test_midi.py

