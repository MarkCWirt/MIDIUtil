Extending the Library
=====================

The choice of MIDI event types included in the library is somewhat
idiosyncratic; I included the events I needed for another software
project I was wrote. You may find that you need additional events in
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

Create a New Event Type
-----------------------

The first order of business is to create a new subclass of the GnericEvent
object of the MIDIFile module. This subclass initializes any specific
instance data that is needed for the MIDI event to be written. In
the case of the tempo event, it is the actual tempo (which is defined
in the MIDI standard to be 60000000 divided by the tempo in beats per
minute). This class should also call the superclass' initializer with
the event time, ordinal, and insertion order,  and set the event type
(a unique string used internally by the software).
In the case of the tempo event:

.. code:: python

    class Tempo(GenericEvent):
        '''A class that encapsulates a tempo meta-event
        '''
        def __init__(self,time,tempo, ordinal=3, insertion_order=0):
            self.tempo = int(60000000 / tempo)
            super(Tempo, self).__init__('tempo', time, ordinal, insertion_order)

Any class that you define should include a type, time, ordinal (see below),
and an insertion order.

``self.ord`` and ``self.insertion_order`` are used to order the events
in the MIDI stream. Events are first ordered in time. Events at the
same time are then ordered by ``self.ord``, with lower numbers appearing
in the stream first. The extant classes in the code all allow the user
to specify an ordinal for the object, but they include default values
that are meant to be reasonable.

Lastly events are sorted on the ``self.insertion_order`` member. This
makes it possible to, say, create a Registered Parameter Number call
from a collection of Control Change events. Since all the CC events will
have the same time and class (and therefore default ordinal), you can control
the order of the events by the order in which you add them to the MIDIFile.

Next, if you want the code to be able to de-duplicate events which may
lay over top of one another, the parent class, ``GenericEvent``, has a
member function called ``__eq__()``. If two events do not coincide in
time or type they are not equal, but it they do the ``__eq__`` function
must be modified to show equality. In the case of the ``Tempo`` class,
two tempo events are considered equivalent if they are the same tempo.
In other words, if there are two tempo events at the same time and
the same tempo, one will be removed in the de-duplication process
(which is the default behavious for ``MIDIFile``, but it can be
turned off). From ``GenericEvent.__eq__()``:

.. code:: python

    if self.type == 'tempo':
        if self.tempo != other.tempo:
            return False

If events are not equivalent, the code should return ``False``. If they are, the
code can be allowed to fall through to its default return of ``True``.

Create an Accessor Function
---------------------------

Next, an accessor function should be added to MIDITrack to create an
event of this type. Continuing the example of the tempo event:

.. code:: python

  def addTempo(self,time,tempo, insertion_order=0):
      '''
      Add a tempo change (or set) event.
      '''
      self.eventList.append(Tempo(time,tempo, insertion_order = insertion_order))

(Most/many MIDI events require a channel specification, but the tempo event
does not.)

The public accessor function is via the MIDIFile object, and must include
the track number to which the event is written. So in ``MIDIFile``:

.. code:: python

  def addTempo(self,track, time,tempo):
      if self.header.numeric_format == 1:
          track = 0
      self.tracks[track].addTempo(time,tempo, insertion_order = self.event_counter)
      self.event_counter = self.event_counter + 1

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

This is the function you will use in your code to create an event of
the desired type.

Modify processEventList()
-------------------------

Next, the logic pertaining to the new event type should be added to
``processEventList()`` function of the ``MIDITrack`` class. In general this code
will create a MIDIEvent object and set its type, time, ordinality, and
any specific information that is needed for the event type. This object
is then added to the MIDIEventList.

The relevant section for the tempo event is:

.. code:: python

    elif thing.type == 'tempo':
        event = MIDIEvent("Tempo", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
        event.tempo = thing.tempo
        self.MIDIEventList.append(event)

THe ``MIDIEvent`` class is expected to have a ``type``, ``time``
(which should be converted from beats to ticks as above), ordinal, and an
insertion order, which are similar to the values in the ``GenericEvent`` class.
You are free, of course, to add any other data items that need to be specified.
In the case of ``Tempo`` this is the tempo to be written.

Write the Event Data to the MIDI Stream
----------------------------------------

The last step is to modify the ``MIDIFile.writeEventsToStream()`` function;
here is where some understanding of the MIDI standard is necessary. The
following code shows the creation of a MIDI tempo event:

.. code:: python

    elif event.type == "Tempo":
        code = 0xFF
        subcode = 0x51
        fourbite = struct.pack('>L', event.tempo)
        threebite = fourbite[1:4]       # Just discard the MSB
        varTime = writeVarLength(event.time)
        for timeByte in varTime:
            self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
        self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
        self.MIDIdata = self.MIDIdata + struct.pack('>B',subcode)
        self.MIDIdata = self.MIDIdata + struct.pack('>B', 0x03)
        self.MIDIdata = self.MIDIdata + threebite

The event.type string ("Tempo") was the one chosen in the processEventList
logic.

The code and sub-code are binary values that come from the MIDI
specification.

Next the data is packed into a three byte structure (or a four byte
structure, discarding the most significant byte). Again, the MIDI
specification determines the number of bytes used in the data payload.

All MIDI events begin with a time, which is stored in a slightly bizarre
variable-length format. This time should be converted to MIDI variable-length
data with the ``writeVarLength()`` function before writing to the stream.
In the MIDI standard's variable length data only seven bits of a word are
used to store data; the eighth bit signifies if more bytes encoding the
value follow. The total length may be 1 to 3 bytes, depending upon the size of
the value encoded. The ``writeVarLength()`` function takes care of this
converssion for you.

Now the data is written to the binary object ``self.MIDIdata``, which is
the actual MIDI-encoded data stream. As per the MIDI standard, first we
write our variable-length time value. Next we add the event type code and
sub-code. Then we write the length of the data payload, which in the case
of the tempo event is three bytes. Lastly, we write the actual payload,
which has been packed into the variable ``threebite``.

The reason that there are separate classes for ``GenericEvent`` and ``MIDIEvent``
is that there need not be a one-to-one correspondance. For example, the
code defines a ``Note`` object, but when this is processed in
``processEventList()`` two ``MIDIEvent`` objects are created, one for
the ``note on`` event, one for the ``note off`` event.

.. code:: python

    if thing.type == 'note':
        event         = MIDIEvent("NoteOn", thing.time * TICKSPERBEAT,
                                    thing.ord, thing.insertion_order)
        event.pitch   = thing.pitch
        event.volume  = thing.volume
        event.channel = thing.channel
        self.MIDIEventList.append(event)

        event = MIDIEvent("NoteOff", (thing.time+ thing.duration) * TICKSPERBEAT,
                                    thing.ord -0.1,
                                    thing.insertion_order)
        event.pitch   = thing.pitch
        event.volume  = thing.volume
        event.channel = thing.channel
        self.MIDIEventList.append(event)

Note that the ``NoteOff`` event is created with a slightly lower ordinality
than the ``NoteOn`` event. This is so that at any given time the note off
events will be processed before the note on events.

Write Some Tests
----------------

Yea, it's a hassle, but you know it's the right thing to do!
