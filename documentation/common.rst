Common Events and Function
==========================

.. currentmodule:: midiutil.MidiFile

This page lists some of the more common things that a user is likely to
do with the MIDI file. It is not exhaustive; see the class reference for a more
complete list of public functions.

Adding Notes
------------

As the MIDI standard is all about music, creating notes will probably be
the lion's share of what you're doing. This is done with the ``addNote()``
function.

.. automethod:: MIDIFile.addNote
  :noindex:

As an example, the following code-fragment adds two notes to an (already
created) MIDIFile object:

.. code:: python

  track    = 0   # Track numbers are zero-origined
  channel  = 0   # MIDI channel number
  pitch    = 60  # MIDI note number
  time     = 0   # In beats
  duration = 1   # In beats
  volume   = 100 # 0-127, 127 being full volume

  MyMIDI.addNote(track,channel,pitch,time,duration,volume)
  time  = 1
  pitch = 61
  MyMIDI.addNote(track,channel,pitch,time,duration,volume)

Add a Tempo
-----------

Every track can have tempos specified (the unit of which is beats per minute).

.. automethod:: MIDIFile.addTempo
  :noindex:

Example:

.. code:: python

  track = 0
  time  = 0   # beats, beginning of track
  tempo = 120 # BPM
  MyMIDI.addTempo(track, time, tempo)

Assign a Name to a Track
------------------------

.. automethod:: MIDIFile.addTrackName
  :noindex:

In general, the time should probably be t=0

Example:

.. code:: python

  track      = 0
  time       = 0
  track_name = "Bassline 1"
  MyMIDI.addTrackName(track, time, track_name)

Adding a Program Change Event
-----------------------------

The program change event tells the the instrument what voice a
certain track should sound. As an example, if the instrument you're
using supports `General MIDI <https://www.midi.org/specifications/item/gm-level-1-sound-set>`_,
you can use the GM numbers to specify the instrument.

**Important Note:** Within this library program numbers are
zero-origined (as they are on a byte-level within the MIDI
standard), but most of the documentation you will see is
musician-centric, so they are usually given as one-origined. So, for example,
if you want to sound a Cello, you would use a program number of 42, not the
43 which is given in the link above.

.. automethod:: MIDIFile.addProgramChange
  :noindex:

Example:

.. code:: python

  track   = 0
  channel = 0
  time    = 8 # Eight beats into the composition
  program = 42 # A Cello

  MyMIDI.addProgramChange(track, channel, time, program)

Writing the File to Disk
------------------------

Ultimately, you'll need to write your data to disk to use it.

.. automethod:: MIDIFile.writeFile
  :noindex:

Example:

.. code:: python

  with open("mymidifile.midi", 'wb') as output_file:
      MyMIDI.writeFile(output_file)

Additional Public Function
--------------------------

The above list is not exhaustive. For example, the library includes methods
to create arbitrary channel control events, SysEx and Universal SysEx events,
Registered Parameter calls and Non-Registered Parameter calls, etc. Please see the
:ref:`ClassRef` for a more complete list of public functions.
