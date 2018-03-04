Creating the MIDIFile Object
============================

The first step in using the library is creating a ``MIDIFile`` object.
There are only a few parameters that need be specified, but they affect
the functioning of the library, so it's good to understand what they do.

The signature of of the ``MIDIFile`` ``__init__()`` function is
as follows:

.. code:: python

  def __init__(self,
            numTracks=1,
            removeDuplicates=True,
            deinterleave=True,
            adjust_origin=False,
            file_format=1,
            ticks_per_quarternote=TICKSPERQUARTERNOTE,
            eventtime_is_ticks=False):

where the parameters do the following:

numTracks
---------

``numTracks`` specifies the number of tracks the MIDI file should have.
It should be set to at least 1 (after all, a MIDI file without tracks isn't
very useful), but it may be set higher for a multi-track file.

This parameter defaults to ``1``.

removeDuplicates
----------------

If set to ``True`` (the default), duplicate notes will be removed from
the file. This is done on a track-by-track basis.

Notes are considered duplicates if they occur at the same time, and have
equivalent pitch, and MIDI channel. If set to ``False`` no attempt is made
to remove notes which appear to be duplicates.

``removeDuplicates()`` also attempts to remove other kinds of duplicates. For
example, if there are two tempo events at the same time and same tempo, they
are considered duplicates.

Of course, it's best not to insert duplicate events in the first place,
but this could be unavoidable in some instances -- for example, if the software
is used in the creation of `Generative Music <https://en.wikipedia.org/wiki/Generative_music>`_
using an algorithm that can create duplication of events.

deinterleave
------------

If ``deinterleave`` is set to ``True`` (the default), an attempt will be made
to remove interleaved notes.

To understand what an *interleaved* note is, it is useful to have some understanding
of the MIDI standard.

To make this library more human-centric, one of the fundamental concepts used is
that of the **note**. But the MIDI standard doesn't have notes; instead, it has
**note on** and **note off** events. These are correlated by channel and pitch.

So if, for example, you create two notes of duration 1 and separated by 1/2 of
a beat, ie:

.. code:: python

  time = 0
  duration = 1
  MyMIDI.addNote(track,channel,pitch,time,duration,volume)
  time = 0.5
  MyMIDI.addNote(track,channel,pitch,time,duration,volume)

you end up with a note on event at 0, another note on event a 0.5, and
two note off events, one at 1.0 and one at 1.5. So when the first note off
event is processed it raises the question: which note on event does it correspond to?
The channel and pitch are the same, so there is some ambiguity in the
way that a hardware or software instrument will respond.

if ``deinterleave`` is ``True`` the library tries to disambiguate the situation
by shifting the first note's off event to be immediately before the second
note's on event. Thus in the example above the first note on would be at 0,
the first note off would be at 0.5, the second note on would also be at
0.5 (but would be processed after the note off at that time), and the last
note off would be at 1.5.

If this parameter is set to ``False`` no events will be shifted.

adjust_origin
-------------

If ``adjust_origin`` is ``True`` the library will find the earliest
event in all the tracks and shift all events so that that time is t=0.
If it is ``False`` no time-shifting will occur. The defaul value is
``False``.

file_format
-----------

This specifies the format of the file to be written. Both format 1 (the default)
and format 2 files are supported.

In the format 1 file there is a separate "tempo" track to which tempo and
time signature events are written. The calls to create these events --
``addTemo()`` and ``addTimeSignature()`` accept a track parameter, but in
a format 1 file these are ignored. In format 2 files they are interpreted
literally (and zero-origined, so that a two track file has indices ``0`` and
``1``).

Track indexing is always zero-based, but with the format 1 file the tempo track
is not indexed. Thus if you create a one track file:

.. code:: python

    MyMIDI = MIDIFile(1, file_format=1)

you would only have ``0`` as a valid index; the tempo track is managed independently
for you. Thus:

.. code:: python

    track = 0
    big_track = 1000
    MyMIDI.addTempo(big_track, 0, 120)
    MyMIDI.addNote(track, 0, 69, 0, 1, 100)

works, even though "track 0" is really the second track in the file, and there is
no track 1000.

ticks_per_quarternote
---------------------

The MIDI ticks per quarter note. Defaults to 960. This defines the
finest level of time resolution available in the file. 120, 240, 384,
480, and 960 are common values.

eventtime_is_ticks
------------------

If set to ``True``, all times passed into the event creation functions
should be specified in ticks. Otherwise they should be specified in
quarter-notes (the default).
