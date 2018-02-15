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

GenericEvent class ``ord`` attribute
====================================
The public API for createing ``Note`` events has arguments for ``time``,
which is where the note starts on the zero-based timeline, and ``duration``,
which is where the note ends, relative to the start time.

However, a Standard MIDI File mimics MIDI messages on the wire, where there
are two separate events to define a played note: a **NoteOn** event, and
later, a **NoteOff** event. So our single ``Note`` event has to be morphed
into a **NoteOn** at the start time, and a corresponding **NoteOff** at
start time + duration. When we do this, the **NoteOff** events are not in
chronological order in the event list. This problem is solved after the
entire event list is created by sorting it by event start time.

However, there is a slight complication with this sorting. What do we do
with two events which start at the same time? What if there is a **NoteOn**
at time 100, a corresponding **NoteOff** at time 120, and another **NoteOn**
at time 120? It turns out that we want the **NoteOff** at 120 to occur
before the **NoteOn** at 120. The author's solution to this problem is
nice: add a secondary sort key to break the tie. This secondary sort key
for **NoteOff** is less than the secondary sort key for **NoteOn**, so
**NoteOff** events will appear before **NoteOn** events which have the same
start time.

The ``ord`` attribute is where this secondary sort key is stored. It suffers
the same needless complexity as the ``type`` attribute: it's actually an
attribute of the class, not of an instance. So I will change it to a
class attribute. I will also improve the name, because ``ord`` is also
the name of a Python built-in function. I will name it ``sec_sort_order``.

In this changeset, ``sec_sort_order`` is still an instance attribute of
class ``MIDIEvent``. This is because ``MIDIEvent`` itself is somewhat of
a poor design, which we won't try to correct in this changeset. We will
correct this problem down the road by doing away with class ``MIDIEvent``.

GenericEvent __eq__() method
============================
Now I will address one of the most glaring design flaws: the
``GenericEvent`` method ``__eq__()`` which knows specifics about derived
classes.

The solution for this flaw is straightforward, and should be fairly obvious
to anyone with more than novice-level experience in Python and Object
Oriented programming: just put the knowledge where it belongs, in the
derived classes.

