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
The public API for creating ``Note`` events has arguments for ``time``,
which is where the note starts on the zero-based timeline, and ``duration``,
which is where the note ends, relative to the start time.

However, a Standard MIDI File mimics MIDI messages on the wire, where there
are two separate events to define a played note: a **NoteOn** event, and
later, a **NoteOff** event. So our single ``Note`` event has to be morphed
into a **NoteOn** at the start time, and a corresponding **NoteOff** at
start time + duration. When we do this, the **NoteOff** events are not in
chronological order in the event list. This problem is solved after the
entire event list is created by sorting it by event start time.

However, there is a slight complication with this sorting. What shall we do
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
a poor design, which I won't try to correct in this changeset. I will
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


class MIDIEvent vs. GenericEvent
================================
There is a class, ``MIDIEvent``, which appears to be almost the same as
class ``GenericEvent``. Except it does not have any derived classes.

The existence and purpose of this class ``MIDIEvent`` is puzzling at
first.  After some reading of the code, it became clear that it is
used as an intermediate form to adapt between what is stored in
a ``GenericEvent`` and what is needed in a Standard MIDI File.

Below is my explanation of what is going on. It is a bit long, but
necessarily so to explain the original flawed design, and how it can be
improved.

A complete MIDI file is represented by the following objects:

    A single ``MIDIFile`` object, which contains a list of ``MIDITrack`` objects.

    Each ``MIDITrack`` contains a list of objects derived from
    ``GenericEvent``, such as ``Note`` objects, ``ProgramChange`` objects,
    etc.

All these objects contain in themselves the attributes needed to create a
Standard MIDI File.

Writing a Standard MIDI File involves writing the sequence of bytes which
are the representation of these objects, as described in the Standard
MIDI File Format Specification, published by the International MIDI
Association. In modern software terminology, this is sometimes called
"serialization".

However, there are a couple of impedance mismatches between what is stored
in a ``GenericEvent`` object and the serialization form which is needed in
a Standard MIDI File:

In a ``GenericEvent``, the start time of the event is stored as "the number
of quarter notes since time zero" (the beginning of the song).  These are
floats, i.e. fractions of a quarter note are possible.  (Note that the
original author of ``midiutil`` made the mistake of calling these "beats",
not quarter notes, causing some confusion to other people but otherwise no
grave harm.)

However, in a SMF, event start time units are integer "ticks", not fractional
quarter notes. The SMF contains a top-level attribute which specifies how many
ticks per quarter note (usually 120, 240, 384, 480, or 960), so conversion
from tick to quarter note units and back is trivial.

Furthermore, in a SMF, the start time of an event is stored as not as the
number of ticks since time zero, but as the number of ticks since the start
of the preceding event. This use of delta ticks instead of absolute ticks
allows a savings of storage space, since most delta times will be small
enough to be expressed in only 7 or 14 bits.

So when it is time to write all the objects to a SMF, each ``MIDITrack``
iterates its list of ``GenericEvent`` objects, and creates a second list, of
``MIDIEvent`` objects. Each ``GenericEvent`` is copied to a ``MIDIEvent``,
so different ``MIDIEvent`` instances contain different attributes depending
on which derived type of ``GenericEvent`` was copied to it. The quarternote
``time`` attribute of ``GenericEvent`` is changed to ticks, and stored in
the ``time`` attribute of ``MIDIEvent``. Furthermore, ``MIDIEvent.time``
is a float, not an int.

See all this in ``MIDITrack.processEventList()``.

This is also where the single ``Note`` event with a start time and duration
is morphed into two ``NoteOn`` and ``NoteOff`` events, each with a start
time.

Finally, since the original list of ``GenericEvent`` was not in chronological
order, this new list of ``MIDIEvent`` is sorted by start time (and secondary
sort order, as mentioned in our previous lesson).

Then, this list of ``MIDIEvent`` objects is iterated, and the attributes
are serialized into the format required by SMF specification.
See ``writeEventsToStream()``, which has all the knowledge of each different
event's .

**This is not a good design.**

To improve it, I will:

1. Throw away the ``MIDIEvent`` class

2. Add a ``tick`` attribute to ``GenericEvent``, and make ``time`` a
   property attribute whose setter also sets the ``tick`` attribute,
   converting the float quarter note time unit to ticks. So ``GenericEvent``
   will have both start time representations.

3. Change the name of the ``Note`` class to ``NoteOn``, and create a
   new class ``NoteOff``, which has the same attributes as ``NoteOn``, i.e.
   channel number, note number (original author named this "pitch"), start
   time, and velocity (which original author misnamed "volume").  Except
   ``NoteOff`` does not have nor need a duration attribute.

4. Change ``MIDITrack.addNoteByNumber()`` to append both a ``NoteOn`` and
   corresponding ``NoteOff`` to the ``MIDITrack.eventList``, with the start
   time of the ``NoteOff`` being the ``NoteOn.time + NoteOn.duration``.
   Previously this was done in ``processEventList()``

5. Then the big mess that is ``processEventList()`` becomes just::

        self.MIDIEventList = [evt for evt in self.eventList]
        self.MIDIEventList.sort(key=sort_events)

6. Finally, all the knowledge of the serialization form of each kind
   of event is removed from ``writeEventsToStream()`` and put where it
   belongs, in each derived class of ``GenericEvent``. The big mess which
   is in ``writeEventsToStream()``, inside the loop
   ``for event in self.MIDIEventList:``  is simplified to::

        for event in self.MIDIEventList:
            self.MIDIdata += event.serialize()


Using ticks instead of fractional quarter notes as time
=======================================================
The public interface of ``MIDIFile`` is designed such that you must specify
the start time and duration of an event in units of quarter notes. Fractions
are acceptable, for example you can specify start time 1.5 to mean one
and half quarter notes from the start of the MIDI file timeline.

The Standard MIDI File as well as almost all MIDI sequencer software stores
start times and durations in units of ticks.  There is in the SMF a number
which tells you how many ticks are in a quarter note, usually 480, 960, or
120. So converting between tick units and quarter note units is
straightforward.

Using quarter notes as start times may be more convenient than ticks if you
are generating musical events programmatically, or writing drum machine
patterns.

However, using ticks as the start time instead quarter notes is more
convenient if you wanted to use ``MIDIFile`` in a project to convert some
old sequence files from some obsolete MIDI software into standard MIDI
format.

The design changes I will make:

``GenericEvent`` will store start time and duration as ticks, not quarter
notes.

I will change the public API of ``MIDIFile`` so you can use either ticks or
quarter notes as the time unit for the ``time`` argument to the ``add...()``
methods. The signatures of all the ``add...()`` methods will remain the
same. And the default time unit will remain quarter notes.

An additional keyword argument, ``eventtime_is_ticks=False``, will be added
to ``MIDIFile.__init__()``.  You can choose to use ticks when you instantiate
``MIDIFile`` by specifying ``eventtime_is_ticks=True``. To maintain backward
compability, the default is ``False``.

I do not particularly like that the ``time`` argument will become dual
personality, but it is the simplest way to allow for using either ticks or
quarter note units. Creating a parallel set of ``add...()`` methods just for
ticks would be another way, but is not appealing.

So after this changset, the external API of ``MIDIFile`` remains the same,
except it offers an option to allow the user to specify time in ticks
instead of quarter notes.

If for some reason you wish to access individual event times as stored in
the ``MIDITrack.eventsList``, and have code which expects the time attribute
to be quarter note value instead of tick, you can convert the tick value to
quarter note value with ``MIDIFile.tick_to_quarter(tickval)``.
