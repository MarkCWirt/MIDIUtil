Extending the Library
=====================

The choice of MIDI event types included in the library is somewhat
idiosyncratic; I included the events I needed for another software
project I was writting. You may find that you need additional events in
your work. For this reason I am including some instructions on extending
the library.  The process isn't too hard (provided you have a working
knowledge of Python and the MIDI standard), so the task shouldn't present
a competent coder too much difficulty. Alternately (if, for example,
you *don't* have a working knowledge of MIDI and don't desire to gain it),
you can submit new feature requests to me, and I will include them into
the development branch of the code, subject to the constraints of time.

To illustrate the process I show below how the MIDI tempo event is
incorporated into the code. This is a relatively simple event, so while
it may not illustrate some of the subtleties of MIDI programing, it
provides a good, illustrative case.

The MID standard defines the Tempo event as the following byte-stream::

  FF 51 03 tttttt

where ``FF 51`` is the code and sub-code of the event, ``03`` is the data
length of the event, and ``tttttt`` are the three bytes of data, encoded as
microseconds per quarter note.

Create a New Event Type
-----------------------

The majority of work involved with creating a new event type is the
creation of a new subclass of the ``GenericEvent``
object of the MIDIFile module. This subclass:

- Initializes any specific instance data that is needed for the MIDI event, and
- Defines how the data are serialized to the byte stream
- Defines the order in which an event is written to the byte stream (see below)

In the case of the tempo, the actual data conversion is easy: people tend
to specify tempos in beats per minute, so the input will need to be divided into
60000000.

The serialization strategy is defined in the subclass' ``serialize`` member
function, which is presented below.

``sec_sort_order`` and ``insertion_order`` are used to order the events
in the MIDI stream. Events are first ordered in time. Events at the
same time are then ordered by ``sec_sort_order``, with lower numbers appearing
in the stream first. Lastly events are sorted on the ``self.insertion_order``
member. This strategy makes it possible to, say, create a Registered Parameter Number call
from a collection of Control Change events. Since all the CC events will
have the same time and class (and therefore default secondary sort order), you can control
the order of the events by the order in which you add them to the MIDIFile.

Al of this will perhaps be more clear if we examine the code:

.. code:: python

  class Tempo(GenericEvent):
      '''
      A class that encapsulates a tempo meta-event
      '''
      evtname = 'Tempo'
      sec_sort_order = 3

      def __init__(self, tick, tempo, insertion_order=0):
          self.tempo = int(60000000 / tempo)
          super(Tempo, self).__init__(tick, insertion_order)

      def __eq__(self, other):
          return (self.evtname == other.evtname and
                  self.tick == other.tick and
                  self.tempo == other.tempo)

      __hash__ = GenericEvent.__hash__

      def serialize(self, previous_event_tick):
          """Return a bytestring representation of the event, in the format required for
          writing into a standard midi file.
          """

          midibytes = b""
          code = 0xFF
          subcode = 0x51
          fourbite = struct.pack('>L', self.tempo)  # big-endian uint32
          threebite = fourbite[1:4]  # Just discard the MSB
          varTime = writeVarLength(self.tick - previous_event_tick)
          for timeByte in varTime:
              midibytes += struct.pack('>B', timeByte)
          midibytes += struct.pack('>B', code)
          midibytes += struct.pack('>B', subcode)
          midibytes += struct.pack('>B', 0x03)  # length in bytes of 24-bit tempo
          midibytes += threebite
          return midibytes


The event name (``evtname``) and secondary sort order are defined in class data; any class that
you create will do the same. ``tick`` is the time in MIDI ticks of the event and
insertion order will be set in the code. All events should accept these
parameters. ``tempo`` is the specific instance data needed for this event type.

The ``__init__()`` member converts the tempo to number needed by the standard and
then calls the super-class' initialization function with tick and insertion order.
All event subclasses should do this.

Next, the ``__eq__()`` function is defined that specifies when two events are
the same. In this case they are the same if the tick, event name, and tempo are
the same. This code is used to identify and remove duplicate events. ``__hash__()``
should explicitly be brought down from the parent class, in in Python 3 it is
not implicitly inherited.

Lastly, the ``serialize`` member function should be created. This will return a
byte stream representing the MIDI data. A few things to note about this:

- All MIDI events begin with a time, which is written in an idiosyncratic
  variable-length format. Use the ``writeVarLength`` utility function to calculate
  this.
- Note that in the case of the tempo event, the standard only uses three bytes,
  whereas in python a long will be packed into four bytes. Hence we just
  discard the MSB.
- In the temo the actual data is packed:
  - The time
  - The code (0xFF)
  - The subcode (0x51)
  - The length of that (defined in the event as 3 bytes)
  - The data proper

Create an Accessor Function
---------------------------

Next, an accessor function should be added to MIDITrack to create an
event of this type. Continuing the example of the tempo event:

.. code:: python

  def addTempo(self, tick, tempo, insertion_order=0):
      '''
      Add a tempo change (or set) event.
      '''
      self.eventList.append(Tempo(tick, tempo,
                            insertion_order=insertion_order))

(Most/many MIDI events require a channel specification, but the tempo event
does not.)

This is more-or-less boilerplate code, and just needs to appropriately create the
object you defined above.

Note that this function can in some cases create multiple events. For example,
when one adds a note, both a ``NoneOn`` and a ``NoteOff`` event will be created.

Lastly, the public accessor function is via the MIDIFile object, and must include
the track number to which the event is written. So in ``MIDIFile``:

.. code:: python

  def addTempo(self, track, time, tempo):
      """

      Add notes to the MIDIFile object

      :param track: The track to which the tempo event  is added. Note that
          in a format 1 file this parameter is ignored and the tempo is
          written to the tempo track
      :param time: The time (in beats) at which tempo event is placed
      :param tempo: The tempo, in Beats per Minute. [Integer]
      """
      if self.header.numeric_format == 1:
          track = 0
      self.tracks[track].addTempo(self.time_to_ticks(time), tempo,
                                  insertion_order=self.event_counter)
      self.event_counter += 1

Note that a track has been added (which is zero-origined and needs to be
constrained by the number of tracks that the ``MIDIFile`` was created with),
and ``insertion_order`` is taken from the class ``event_counter``
data member. This should be followed in each function you add. Also note that
the tempo event is handled differently in format 1 files and format 2 files.
This function ensures that the tempo event is written to the first track
(track 0) for a format 1 file, otherwise it writes it to the track specified.
In most of the public functions a check it done on format, and the track is
incremented by one for format 1 files so that the event is not written to the
tempo track (but preserving the zero-origined convention for all tracks in
both formats.)

The only other complexity is that the public functions accept by default a time
in quarter-notes, not MIDI ticks. So the public accessor function should
pass the time through the ``time_to_ticks()`` member. If the MIDIFile was
instantiated with ``eventtime_is_ticks = True``, this is just an identity fucntion
and the public accessor will expect time in ticks. Otherwise it will convert from
quarter-notes to ticks (suing the ``TICKSPERQUARTERNOTE`` instance data)

This is the function you will use in your code to create an event of
the desired type.

Write Some Tests
----------------

Yea, it's a hassle, but you know it's the right thing to do!
