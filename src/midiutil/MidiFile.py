#-----------------------------------------------------------------------------
# Name:        MidiFile.py
# Purpose:     MIDI file manipulation utilities
#
# Author:      Mark Conway Wirt <emergentmusics) at (gmail . com>
#
# Created:     2008/04/17
# Copyright:   (c) 2009-2016 Mark Conway Wirt
# License:     Please see License.txt for the terms under which this
#              software is distributed.
#-----------------------------------------------------------------------------

from __future__ import division, print_function
import struct,  math, warnings

# TICKSPERBEAT is the number of "ticks" (time measurement in the MIDI file) that
# corresponds to one beat. This number is somewhat arbitrary, but should be chosen
# to provide adequate temporal resolution.

TICKSPERBEAT = 960

controllerEventTypes = {
    'pan' : 0x0a
}

# Define some constants

MAJOR  = 0
MINOR  = 1
SHARPS = 1
FLATS  = -1

__all__ = ['MIDIFile', 'MAJOR', 'MINOR', 'SHARPS', 'FLATS']

class MIDIEvent(object):
    '''
    The class to contain the MIDI Event (placed on MIDIEventList).
    '''
    def __init__(self, type="unknown", time = 0, ordinal=0, insertion_order=0):
        self.type=type
        self.time=time
        self.ord = ordinal
        self.insertion_order=insertion_order

class GenericEvent(object):
    '''
    The event class from which specific events are derived
    '''
    def __init__(self, event_type, time, ordinal, insertion_order):
        self.type = event_type
        self.time = time 
        self.ord = ordinal
        self.insertion_order = insertion_order
        #self.type = 'Unknown'

        
    def __eq__(self, other):
        '''
        Equality operator for Generic Events and derived classes.
        
        In the processing of the event list, we have need to remove duplicates. To do this
        we rely on the fact that the classes are hashable, and must therefore have an 
        equality operator (__hash__() and __eq__() must both be defined).
        
        This is the most embarrassing portion of the code, and anyone who knows about OO
        programming would find this almost unbelievable. Here we have a base class that
        knows specifics about derived classes, thus breaking the very spirit of 
        OO programming.
        
        I suppose I should go back and restructure the code, perhaps removing the derived
        classes altogether. At some point perhaps I will.
        '''
        if self.time != other.time or self.type != other.type:
            return False
            
        # What follows is code that encodes the concept of equality for each derived 
        # class. Believe it f you dare.
        
        if self.type == 'note':
            if self.pitch != other.pitch or self.channel != other.channel:
                return False
        if self.type == 'tempo':
            if self.tempo != other.tempo:
                return False
        if self.type == 'programChange':
            if self.programNumber != other.programNumber or self.channel != other.channel:
                return False
        if self.type == 'trackName':
            if self.trackName != other.trackName:
                return False
        if self.type == 'controllerEvent':
            return False
                
        if self.type == 'SysEx':
            return False
                
        if self.type == 'UniversalSysEx':
            return False
                
        return True
        
    def __hash__(self):
        '''
        Return a hash code for the object.
        
        This is needed for the removal of duplicate objects from the event list. The only
        real requirement for the algorithm is that the hash of equal objects must be equal.
        There is probably great opportunity for improvements in the hashing function.
        '''
        # Robert Jenkin's 32 bit hash.
        a = int(self.time)
        a = (a+0x7ed55d16) + (a<<12)
        a = (a^0xc761c23c) ^ (a>>19)
        a = (a+0x165667b1) + (a<<5)
        a = (a+0xd3a2646c) ^ (a<<9)
        a = (a+0xfd7046c5) + (a<<3)
        a = (a^0xb55a4f09) ^ (a>>16)
        return a

class Note(GenericEvent):
    '''
    A class that encapsulates a note
    '''
    def __init__(self,channel, pitch,time,duration,volume,ordinal=3,annotation=None, insertion_order=0):
        self.pitch = pitch
        self.duration = duration
        self.volume = volume
        self.channel = channel
        self.annotation = annotation
        super(Note, self).__init__('note', time, ordinal, insertion_order)
        
class Tempo(GenericEvent):
    '''
    A class that encapsulates a tempo meta-event
    '''
    def __init__(self,time,tempo, ordinal=3, insertion_order=0):
        self.tempo = int(60000000 / tempo)
        super(Tempo, self).__init__('tempo', time, ordinal, insertion_order)
        
class Copyright(GenericEvent):
    '''
    A class that encapsulates a copyright event
    '''
    def __init__(self,time,notice, ordinal=1, insertion_order=0):
        self.notice = notice.encode("ISO-8859-1")
        super(Copyright, self).__init__('Copyright', time, ordinal, insertion_order)
        
class Text(GenericEvent):
    '''
    A class that encapsulates a text event
    '''
    def __init__(self, time, text, ordinal=1, insertion_order=0):
        self.text = text.encode("ISO-8859-1")
        super(Text, self).__init__('Text', time, ordinal, insertion_order)
        
class KeySignature(GenericEvent):
    '''
    A class that encapsulates a text event
    '''
    def __init__(self, time, accidentals, accidental_type, mode, ordinal=1, insertion_order=0):
        self.accidentals = accidentals
        self.accidental_type = accidental_type
        self.mode = mode
        super(KeySignature, self).__init__('KeySignature', time, ordinal, insertion_order)
        
class ProgramChange(GenericEvent):
    '''
    A class that encapsulates a program change event.
    '''
    
    def __init__(self,  channel,  time,  programNumber, ordinal=1, insertion_order=0):
        self.programNumber = programNumber
        self.channel = channel
        super(ProgramChange, self).__init__('programChange', time, ordinal, insertion_order)
        
class SysExEvent(GenericEvent):
    '''
    A class that encapsulates a System Exclusive  event.
    '''
    
    def __init__(self,  time,  manID,  payload, ordinal=1, insertion_order=0):
        self.manID = manID
        self.payload = payload
        super(SysExEvent, self).__init__('SysEx', time, ordinal, insertion_order)
        
class UniversalSysExEvent(GenericEvent):
    '''
    A class that encapsulates a Universal System Exclusive  event.
    '''
    
    def __init__(self,  time,  realTime,  sysExChannel,  code,  subcode,  payload, 
                 ordinal=1, insertion_order=0):
        self.realTime = realTime
        self.sysExChannel = sysExChannel
        self.code = code
        self.subcode = subcode
        self.payload = payload
        super(UniversalSysExEvent, self).__init__('UniversalSysEx', time, ordinal, insertion_order)
        
class ControllerEvent(GenericEvent):
    '''
    A class that encapsulates a program change event.
    '''
    
    def __init__(self,  channel,  time,  controller_number, parameter, ordinal=1, insertion_order=0):
        self.parameter = parameter
        self.channel = channel
        self.controller_number = controller_number
        super(ControllerEvent, self).__init__('controllerEvent', time, ordinal, insertion_order)

class TrackName(GenericEvent):
    '''
    A class that encapsulates a program change event.
    '''
    
    def __init__(self,  time,  trackName, ordinal=0, insertion_order=0):
        #GenericEvent.__init__(self, time,)
        self.trackName = trackName.encode("ISO-8859-1")
        super(TrackName, self).__init__('trackName', time, ordinal, insertion_order)
        
class TimeSignature(GenericEvent):
    '''
    A class that encapsulates a time signature.
    '''
    
    def __init__(self,  time,  numerator, denominator, clocks_per_tick, notes_per_quarter, ordinal=0, insertion_order=0):
        self.numerator = numerator
        self.denominator = denominator
        self.clocks_per_tick = clocks_per_tick
        self.notes_per_quarter = notes_per_quarter
        super(TimeSignature, self).__init__('TimeSignature', time, ordinal, insertion_order)
        
class MIDITrack(object):
    '''
    A class that encapsulates a MIDI track
    '''                        
            
    def __init__(self, removeDuplicates,  deinterleave):
        '''Initialize the MIDITrack object.
        '''
        self.headerString = struct.pack('cccc',b'M',b'T',b'r',b'k')
        self.dataLength = 0 # Is calculated after the data is in place
        self.MIDIdata = b""
        self.closed = False
        self.eventList = []
        self.MIDIEventList = []
        self.remdep = removeDuplicates
        self.deinterleave = deinterleave
        
    def addNoteByNumber(self,channel, pitch,time,duration,volume,annotation=None, 
                        insertion_order=0):
        '''
        Add a note by chromatic MIDI number
        '''
        self.eventList.append(Note(channel, pitch,time,duration,volume,annotation=annotation,
                                   insertion_order = insertion_order))
        
    def addControllerEvent(self,channel,time,controller_number, parameter, insertion_order=0):
        '''
        Add a controller event.
        '''
        
        self.eventList.append(ControllerEvent(channel,time,controller_number, \
                                             parameter, insertion_order=insertion_order))
        
    def addTempo(self,time,tempo, insertion_order=0):
        '''
        Add a tempo change (or set) event.
        '''
        self.eventList.append(Tempo(time,tempo, insertion_order = insertion_order))
        
    def addSysEx(self,time,manID, payload, insertion_order=0):
        '''
        Add a SysEx event.
        '''
        self.eventList.append(SysExEvent(time, manID,  payload, 
                                         insertion_order = insertion_order))
        
    def addUniversalSysEx(self,time,code, subcode, payload,  sysExChannel=0x7F,  \
        realTime=False, insertion_order = 0):
        '''
        Add a Universal SysEx event.
        '''
        self.eventList.append(UniversalSysExEvent(time, realTime,  \
            sysExChannel,  code,  subcode, payload, insertion_order = insertion_order))
        
    def addProgramChange(self,channel, time, program, insertion_order=0):
        '''
        Add a program change event.
        '''
        self.eventList.append(ProgramChange(channel, time, program, insertion_order = insertion_order))
        
    def addTrackName(self,time,trackName, insertion_order = 0):
        '''
        Add a track name event.
        '''
        self.eventList.append(TrackName(time,trackName, insertion_order = insertion_order))
        
    def addTimeSignature(self, time, numerator, denominator, clocks_per_tick, notes_per_quarter, insertion_order = 0):
        '''
        Add a time signature.
        '''
        self.eventList.append(TimeSignature(time, numerator, denominator, 
                                            clocks_per_tick, notes_per_quarter, insertion_order = insertion_order))
                                            
    def addCopyright(self, time, notice, insertion_order = 0):
        '''
        Add a copyright notice
        '''
        self.eventList.append(Copyright(time, notice, insertion_order = insertion_order))
        
    def addKeySignature(self, time, accidentals, accidental_type, mode, insertion_order = 0):
        '''
        Add a copyright notice
        '''
        self.eventList.append(KeySignature(time, accidentals, accidental_type, mode, 
                                        insertion_order = insertion_order))
        
    def addText(self, time, text, insertion_order = 0):
        '''
        Add a text event
        '''
        self.eventList.append(Text(time, text, insertion_order = insertion_order))
        
    def changeNoteTuning(self,  tunings,   sysExChannel=0x7F,  realTime=True,  \
        tuningProgam=0, insertion_order=0):
        '''
        Change the tuning of MIDI notes
        '''
        payload = struct.pack('>B',  tuningProgam)
        payload = payload + struct.pack('>B',  len(tunings))
        for (noteNumber,  frequency) in tunings:
            payload = payload + struct.pack('>B',  noteNumber)
            MIDIFreqency = frequencyTransform(frequency)
            for byte in MIDIFreqency:
                payload = payload + struct.pack('>B',  byte)
                
        self.eventList.append(UniversalSysExEvent(0, realTime,  sysExChannel,\
            8,  2, payload, insertion_order = insertion_order))
    
    def processEventList(self):
        '''
        Process the event list, creating a MIDIEventList
        
        For each item in the event list, one or more events in the MIDIEvent
        list are created.
        '''
        
        # Loop over all items in the eventList
        
        for thing in self.eventList:
            if thing.type == 'note':
                event         = MIDIEvent("NoteOn", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
                event.pitch   = thing.pitch
                event.volume  = thing.volume
                event.channel = thing.channel
                self.MIDIEventList.append(event)

                event         = MIDIEvent("NoteOff", (thing.time+ thing.duration) * TICKSPERBEAT, thing.ord -0.1,
                                            thing.insertion_order)
                event.pitch   = thing.pitch
                event.volume  = thing.volume
                event.channel = thing.channel
                self.MIDIEventList.append(event)

            elif thing.type == 'tempo':
                event = MIDIEvent("Tempo", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
                event.tempo = thing.tempo
                self.MIDIEventList.append(event)
                
            elif thing.type == 'Copyright':
                event = MIDIEvent("Copyright", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
                event.notice = thing.notice
                self.MIDIEventList.append(event)
                
            elif thing.type == 'Text':
                event = MIDIEvent("Text", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
                event.text = thing.text
                self.MIDIEventList.append(event)
                
            elif thing.type == 'KeySignature':
                event = MIDIEvent("KeySignature", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
                event.accidentals     = thing.accidentals
                event.accidental_type = thing.accidental_type
                event.mode            = thing.mode
                self.MIDIEventList.append(event)
                
            elif thing.type == 'programChange':
                event               = MIDIEvent("ProgramChange", thing.time * TICKSPERBEAT, thing.ord, 
                                                thing.insertion_order)
                event.programNumber = thing.programNumber
                event.channel       = thing.channel
                self.MIDIEventList.append(event)

            elif thing.type == 'trackName':
                event = MIDIEvent("TrackName", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
                event.trackName = thing.trackName
                self.MIDIEventList.append(event)

            elif thing.type == 'controllerEvent':
                event = MIDIEvent("ControllerEvent", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
                event.controller_number = thing.controller_number
                event.channel = thing.channel
                event.parameter = thing.parameter
                self.MIDIEventList.append(event)

            elif thing.type == 'SysEx':
                event = MIDIEvent("SysEx", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
                event.manID = thing.manID
                event.payload = thing.payload
                self.MIDIEventList.append(event)

            elif thing.type == 'UniversalSysEx':
                event = MIDIEvent("UniversalSysEx", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
                event.realTime = thing.realTime
                event.sysExChannel = thing.sysExChannel
                event.code = thing.code
                event.subcode = thing.subcode
                event.payload = thing.payload
                self.MIDIEventList.append(event)
                
            elif thing.type == 'TimeSignature':
                event = MIDIEvent("TimeSignature", thing.time * TICKSPERBEAT, thing.ord, thing.insertion_order)
                event.numerator = thing.numerator
                event.denominator = thing.denominator
                event.clocks_per_tick = thing.clocks_per_tick
                event.notes_per_quarter = thing.notes_per_quarter
                self.MIDIEventList.append(event)

            else:
                raise ValueError("Error in MIDITrack: Unknown event type %s" % thing.type)
            
        # Assumptions in the code expect the list to be time-sorted.
        self.MIDIEventList.sort(key=sort_events)

        if self.deinterleave:    
            self.deInterleaveNotes()

    def removeDuplicates(self):
        '''
        Remove duplicates from the eventList.
        
        This function will remove duplicates from the eventList. This is necessary
        because we the MIDI event stream can become confused otherwise.
        '''
        
        # For this algorithm to work, the events in the eventList must be hashable 
        # (that is, they must have a __hash__() and __eq__() function defined).

        tempDict = {}
        for item in self.eventList:
            tempDict[item] = 1
            
        self.eventList = list(tempDict.keys())
        
        self.eventList.sort(key=sort_events)


    def closeTrack(self):
        '''
        Called to close a track before writing
        
        This function should be called to "close a track," that is to
        prepare the actual data stream for writing. Duplicate events are
        removed from the eventList, and the MIDIEventList is created.
        
        Called by the parent MIDIFile object.
        '''

        if self.closed == True:
            return
        self.closed = True
        
        if self.remdep:
            self.removeDuplicates()
            

        self.processEventList()
        
    def writeMIDIStream(self):
        '''
        Write the meta data and note data to the packed MIDI stream.
        '''

        #Process the events in the eventList

        self.writeEventsToStream()

        # Write MIDI close event.

        self.MIDIdata = self.MIDIdata + struct.pack('BBBB',0x00,0xFF, \
            0x2F,0x00)
        
        # Calculate the entire length of the data and write to the header
        
        self.dataLength = struct.pack('>L',len(self.MIDIdata))

    def writeEventsToStream(self):
        '''
        Write the events in MIDIEvents to the MIDI stream.
        '''
        preciseTime = 0.0                   # Actual time of event, ignoring round-off
        actualTime = 0.0                    # Time as written to midi stream, include round-off
        for event in self.MIDIEventList:

            preciseTime = preciseTime + event.time

            # Convert the time to variable length and back, to see how much
            # error is introduced

            testBuffer = b""
            varTime = writeVarLength(event.time)
            for timeByte in varTime:
                testBuffer = testBuffer + struct.pack('>B',timeByte)
            (roundedVal,discard) = readVarLength(0,testBuffer)
            roundedTime = actualTime + roundedVal

            # Calculate the delta between the two and apply it to the event time.

            delta = preciseTime - roundedTime
            event.time = event.time + delta

            # Now update the actualTime value, using the updated event time.

            testBuffer = b""
            varTime = writeVarLength(event.time)
            for timeByte in varTime:
                testBuffer = testBuffer + struct.pack('>B',timeByte)

            (roundedVal,discard) = readVarLength(0,testBuffer)
            actualTime = actualTime + roundedVal
        
        for event in self.MIDIEventList:
            if event.type == "NoteOn":
                code = 0x9 << 4 | event.channel
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.pitch)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.volume)
            elif event.type == "NoteOff":
                code = 0x8 << 4 | event.channel
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.pitch)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.volume)
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
            elif event.type == "Text":
                code = 0xFF
                subcode = 0x01
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)                
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',subcode)
                payloadLength = len(event.text)
                payloadLengthVar = writeVarLength(payloadLength)
                for i in range(len(payloadLengthVar)):
                    self.MIDIdata = self.MIDIdata + struct.pack("b",payloadLengthVar[i])
                self.MIDIdata = self.MIDIdata + event.text
            elif event.type == "Copyright":
                code = 0xFF
                subcode = 0x02
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)                
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',subcode)
                payloadLength = len(event.notice)
                payloadLengthVar = writeVarLength(payloadLength)
                for i in range(len(payloadLengthVar)):
                    self.MIDIdata = self.MIDIdata + struct.pack("b",payloadLengthVar[i])
                self.MIDIdata = self.MIDIdata + event.notice
            elif event.type == "TimeSignature":
                code = 0xFF
                subcode = 0x58
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',subcode)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', 0x04)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.numerator)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.denominator)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.clocks_per_tick)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.notes_per_quarter) # 32nd notes per quarter note
            elif event.type == "KeySignature":
                code = 0xFF
                subcode = 0x59
                event_subtype = 0x02
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',subcode)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event_subtype)
                self.MIDIdata = self.MIDIdata + struct.pack('>b',event.accidentals * event.accidental_type)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.mode)
            elif event.type == 'ProgramChange':
                code = 0xC << 4 | event.channel
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.programNumber)
            elif event.type == 'TrackName':
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('B',0xFF)
                self.MIDIdata = self.MIDIdata + struct.pack('B',0X03)
                dataLength = len(event.trackName)
                dataLenghtVar = writeVarLength(dataLength)
                for i in range(0,len(dataLenghtVar)):
                    self.MIDIdata = self.MIDIdata + struct.pack("b",dataLenghtVar[i])
                self.MIDIdata = self.MIDIdata + event.trackName
            elif event.type == "ControllerEvent":
                code = 0xB << 4 | event.channel
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.controller_number)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.parameter)
            elif event.type == "SysEx":
                code = 0xF0
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', code)
                
                payloadLength = writeVarLength(len(event.payload)+2)
                for lenByte in payloadLength:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',lenByte)
                    
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.manID)
                self.MIDIdata = self.MIDIdata + event.payload
                self.MIDIdata = self.MIDIdata + struct.pack('>B',0xF7)
            elif event.type == "UniversalSysEx":
                code = 0xF0
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', code)
                
                # Do we need to add a length?
                payloadLength = writeVarLength(len(event.payload)+5)
                for lenByte in payloadLength:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',lenByte)
                
                if event.realTime :
                    self.MIDIdata = self.MIDIdata + struct.pack('>B', 0x7F)
                else:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B', 0x7E)
                    
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.sysExChannel)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.subcode)
                self.MIDIdata = self.MIDIdata + event.payload
                self.MIDIdata = self.MIDIdata + struct.pack('>B',0xF7)
        
    def deInterleaveNotes(self):
        '''
        Correct Interleaved notes.
        
        Because we are writing multiple notes in no particular order, we
        can have notes which are interleaved with respect to their start
        and stop times. This method will correct that. It expects that the
        MIDIEventList has been time-ordered.
        '''
        
        tempEventList = []
        stack = {}
        
        for event in self.MIDIEventList:
            
            if event.type == 'NoteOn':
                if str(event.pitch)+str(event.channel) in stack:
                    stack[str(event.pitch)+str(event.channel)].append(event.time)
                else:
                    stack[str(event.pitch)+str(event.channel)] = [event.time]
                tempEventList.append(event)
            elif event.type == 'NoteOff':
                if len(stack[str(event.pitch)+str(event.channel)]) > 1:
                    event.time = stack[str(event.pitch)+str(event.channel)].pop()
                    tempEventList.append(event)
                else:
                    stack[str(event.pitch)+str(event.channel)].pop()
                    tempEventList.append(event)
            else:
                tempEventList.append(event)
                    
        self.MIDIEventList = tempEventList
        
        # Note that ``processEventList`` makes the ordinality of a note off event
        # a bit lower than the note on event, so this sort will make concomitant
        # note off events processed first.
        
        self.MIDIEventList.sort(key=sort_events)

    def adjustTimeAndOrigin(self,origin, adjust):
        '''
        Adjust Times to be relative, and zero-origined.
        
        If adjust is True, the track will be shifted. Regardelss times
        are converted to relative values here.
        '''
        
        if len(self.MIDIEventList) == 0:
            return
        tempEventList = []
        
        if adjust:
            internal_origin = origin
        else:
            internal_origin = 0.0
    
        runningTime = 0 
        
        for event in self.MIDIEventList:
            adjustedTime = event.time - internal_origin
            event.time = adjustedTime - runningTime
            runningTime = adjustedTime
            tempEventList.append(event)
            
        self.MIDIEventList = tempEventList
        
    def writeTrack(self,fileHandle):
        '''
        Write track to disk.
        '''
            
        fileHandle.write(self.headerString)
        fileHandle.write(self.dataLength)
        fileHandle.write(self.MIDIdata)


class MIDIHeader(object):
    '''
    Class to encapsulate the MIDI header structure.
    
    This class encapsulates a MIDI header structure. It isn't used for much,
    but it will create the appropriately packed identifier string that all
    MIDI files should contain. It is used by the MIDIFile class to create a
    complete and well formed MIDI pattern.
    
    '''
    def __init__(self,numTracks, file_format):
        ''' Initialize the data structures
        '''
        self.headerString = struct.pack('cccc',b'M',b'T',b'h',b'd')
        self.headerSize = struct.pack('>L',6)
        # Format 1 = multi-track file
        self.format = struct.pack('>H',file_format)
        self.numeric_format = file_format
        if file_format == 1:
            delta = 1
        else:
            delta = 0
        self.numTracks = struct.pack('>H',numTracks + delta)
        self.ticksPerBeat = struct.pack('>H',TICKSPERBEAT)
    

    def writeFile(self,fileHandle):
        fileHandle.write(self.headerString)
        fileHandle.write(self.headerSize)
        fileHandle.write(self.format)
        fileHandle.write(self.numTracks)
        fileHandle.write(self.ticksPerBeat)

class MIDIFile(object):
    '''
    A class that encapsulates a full, well-formed MIDI file object.
    
    This is a container object that contains a header (:class:`MIDIHeader`), 
    one or more tracks (class:`MIDITrack`), and the data associated with a proper 
    and well-formed MIDI file.
    '''
    
    def __init__(self, numTracks=1, removeDuplicates=True,  deinterleave=True, adjust_origin=None, file_format=1):
        '''
        
            Initialize the MIDIFile class
            
            :param numTracks: The number of tracks the file contains. Integer, one or greater
            :param removeDuplicates: If set to ``True`` remove duplicate events before writing
                to disk
            :param deinterleave: If set to ``True`` deinterleave the notes in the stream
            :param adjust_origin: If set to ``True`` (or left at the default of ``None``) shift all the
                events in the tracks so that the first event takes place at time t=0
            :param file_format: The format of the multi-track file. This should either be ``1`` (the default,
                and the most widely supported format) or ``2``.
                
            Note that the default for ``adjust_origin`` will change in a future release, so one should probably
            explicitly set it.
            
            Example:
            
            .. code::
            
                # Create a two-track MIDIFile
            
                from midiutil.MidiFile import MIDIFile
                midi_file = MIDIFile(2)
                
            A Note on File Formats
            ----------------------
            
            In previous versions of this code the file written was format 2 (which can be thought of as
            a collection of independent tracks) but was identified as format 1. In this version
            one can specify either format 1 or 2.
            
            In format 1 files there is a separate tempo track which contains tempo and time signature data,
            but contains no note data. If one creates a single track format 1 file the actual file has
            two tracks -- one for tempo data and one for note data. In the track indexing the tempo track
            can be ignored. In other words track 0 is the note track (the second track in the file). However,
            tempo and time signature data will be written to the first, tempo track. This is done to
            try and preserve as much interoperability with previous versions as possible.
            
            In a format 2 file all tracks are indexed and the track parameter is interpreted literally.
        '''
        self.header = MIDIHeader(numTracks, file_format)
        
        self.tracks = list()
        if file_format == 1:
            delta = 1
        else:
            delta = 0
        self.numTracks = numTracks + delta
        self.closed = False
        if adjust_origin is None:
            self.adjust_origin = True
            warnings.warn("Please explicitly set adjust_origin. Default behaviour will change in a future version.", 
                          FutureWarning)
        else:
            self.adjust_origin = adjust_origin
        
        for i in range(0,self.numTracks):
            self.tracks.append(MIDITrack(removeDuplicates,  deinterleave))
            
        self.event_counter = 0 # to keep track of the order of insertion for new sorting
            
            
    # Public Functions. These (for the most part) wrap the MIDITrack functions, where most
    # Processing takes place.
    
    def addNote(self,track, channel, pitch, time, duration, volume, annotation=None):
        """
        
        Add notes to the MIDIFile object
        
        :param track: The track to which the note is added.
        :param channel: the MIDI channel to assign to the note. [Integer, 0-15]
        :param pitch: the MIDI pitch number [Integer, 0-127].
        :param time: the time (in beats) at which the note sounds [Float].
        :param duration: the duration of the note (in beats) [Float].
        :param volume: the volume (velocity) of the note. [Integer, 0-127].
        :param annotation: Arbitrary data to attach to the note.
        
        The ``annotation`` parameter attaches arbitrary data to the note. This 
        is not used in the code, but can be useful anyway. As an example,
        I have created a project that uses MIDIFile to write 
        `csound <http://csound.github.io/>`_ orchestra files directly from the
        class ``EventList``.
        """
        if self.header.numeric_format == 1:
            track = track + 1
        self.tracks[track].addNoteByNumber(channel, pitch, time, duration, volume, 
            annotation = annotation, insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1

    def addTrackName(self,track, time,trackName):
        """
        Name a track.
        
        :param track: The track to which the name is assigned.
        :param time: The time (in beats) at which the track name event is placed.
            In general this should probably be time 0 (the beginning of the track).
        :param trackName: The name to assign to the track [String]
        """
        if self.header.numeric_format == 1:
            track = track + 1
        self.tracks[track].addTrackName(time,trackName, insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1
        
    def addTimeSignature(self, track, time, numerator, denominator, clocks_per_tick, notes_per_quarter = 8):
        '''
        Add a time signature event.
        
        :param track: The track to which the signature is assigned. Note that in
            a format 1 file this parameter is ignored and the event is written to the tempo
            track
        :param time: The time (in beats) at which the event is placed.
            In general this should probably be time 0 (the beginning of the track).
        :param numerator: The numerator of the time signature. [Int]
        :param denominator: The denominator of the time signature, expressed as
            a power of two (see below). [Int]
        :param clocks_per_tick: The number of MIDI clock ticks per metronome 
            click (see below).
        :param notes_per_quarter: The number of annotated 32nd notes in a MIDI
            quarter note. This is almost always 8 (the default), but some
            sequencers allow this value to be changed. Unless you know that your
            sequencing software supports it, this should be left at its default
            value.
        
        The data format for this event is a little obscure. 
        
        The ``denominator`` should be specified as a power of 2, with
        a half note being one, a quarter note being two, and eight note
        being three, etc. Thus, for example, a 4/4 time signature would
        have a ``numerator`` of 4 and a ``denominator`` of 2. A 7/8 time
        signature would be a ``numerator`` of 7 and a ``denominator``
        of 3.

        The ``clocks_per_tick`` argument specifies the number of clock
        ticks per metronome click. By definition there are 24 ticks in
        a quarter note, so a metronome click per quarter note would be
        24. A click every third eighth note would be 3 * 12 = 36.  
        '''
        if self.header.numeric_format == 1:
            track = 0

        self.tracks[track].addTimeSignature(time, numerator, denominator,
            clocks_per_tick, notes_per_quarter, insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1

    def addTempo(self,track, time,tempo):
        """

        Add notes to the MIDIFile object

        :param track: The track to which the tempo event  is added. Note that in a format
            1 file this parameter is ignored and the tempo is written to the tempo track
        :param time: The time (in beats) at which tempo event is placed 
        :param tempo: The tempo, in Beats per Minute. [Integer]
        """ 
        if self.header.numeric_format == 1:
            track = 0        
        self.tracks[track].addTempo(time,tempo, insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1
        
    def addCopyright(self,track, time, notice):
        """

        Add a copyright notice to the MIDIFile object

        :param track: The track to which the notice is added.
        :param time: The time (in beats) at which notice event is placed. In general
            this sould be time t=0
        :param notice: The copyright notice [String]
        """ 
        if self.header.numeric_format == 1:
            track = track + 1        
        self.tracks[track].addCopyright(time,notice, insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1
        
    def addKeySignature(self, track, time, accidentals, accidental_type, mode, insertion_order = 0):
        '''
        Add a Key Signature to a track
        
        :param track: The track to which this should be added
        :param time: The time at which the signature should be placed
        :param accidentals: The number of accidentals in the key signature
        :param accidental_type: The type of accidental
        :param mode: The mode of the scale
        
        The easiest way to use this function is to make sure that the symbolic
        constants for accidental_type and mode are imported. By doing this:
        
        .. code::
        
            from midiutil.MidiFile import *
            
        one gets the following constants defined:
        
        * ``SHARPS``
        * ``FLATS``
        * ``MAJOR``
        * ``MINOR``
        
        So, for example, if one wanted to create a key signature for a minor
        scale with three sharps:
        
        .. code::
        
            MyMIDI.addKeySignature(0, 0, 3, SHARPS, MINOR)
        '''
        if self.header.numeric_format == 1:
            track = track + 1
        self.tracks[track].addKeySignature(time, accidentals, accidental_type, mode, 
            insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1
        
    def addText(self,track, time, text):
        """

        Add a text event

        :param track: The track to which the notice is added.
        :param time: The time (in beats) at which text event is placed.
        :param text: The text to adde [ASCII String]
        """ 
        if self.header.numeric_format == 1:
            track = track + 1
        self.tracks[track].addText(time, text, insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1

    def addProgramChange(self,track, channel, time, program):
        """

        Add a MIDI program change event.

        :param track: The track to which program change event is added.
        :param channel: the MIDI channel to assign to the event. [Integer, 0-15] 
        :param time: The time (in beats) at which the program change event is placed [Float].  
        :param program: the program number. [Integer, 0-127].
        """ 
        self.tracks[track].addProgramChange(channel, time, program,
            insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1

    def addControllerEvent(self,track, channel, time, controller_number, parameter):
        """

        Add a channel control event

        :param track: The track to which the event is added.  
        :param channel: the MIDI channel to assign to the event. [Integer, 0-15] 
        :param time: The time (in beats) at which the event is placed [Float].  
        :param controller_number: The controller ID of the event.  
        :param parameter: The event's parameter, the meaning of which varies by event type.
        """
        if self.header.numeric_format == 1:
            track = track + 1
        self.tracks[track].addControllerEvent(channel,time,controller_number, parameter,
            insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1

    def makeRPNCall(self, track, channel, time, controller_msb, controller_lsb, data_msb, 
                    data_lsb, time_order=False):
        '''

        Perform a Registered Parameter Number Call

        :param track: The track to which this applies 
        :param channel: The channel to which this applies 
        :param time: The time of the event 
        :param controller_msb: The Most significant byte of the controller. In common usage
            this will usually be 0
        :param controller_lsb: The Least significant Byte for the controller message. For example, for
            a fine-tuning change this would be 01.
        :param data_msb: The Most Significant Byte of the controller's parameter.  
        :param data_lsb: The Least Significant Byte of the controller's parameter. If non needed this
            should be set to ``None``
        :param time_order: Order the control events in time (see below)

        As an example, if one were to change a channel's tuning program::

            makeRPNCall(track, channel, time, 0, 3, 0, program)

        (Note, however, that there is a convenience function,
        ``changeTuningProgram``, that does this for you.)
        
        The ``time_order`` parameter is something of a work-around for sequencers that
        do not preserve the order of events from the MIDI files they import. Within this code
        care is taken to preserve the order of events as specified, but some sequencers
        seem to transmit events occurring at the same time in an arbitrary order.
        By setting this parameter to ``True`` something of a work-around is performed: each
        successive event (of which there are three or four for this event type) is placed
        in the time stream a small delta from the preceding one. Thus, for example, the
        controllers are set before the data bytes in this call.
        ''' 
        if self.header.numeric_format == 1:
            track = track + 1
        
        if time_order:
            delta = 1.0 / (TICKSPERBEAT - 10)
        else:
            delta = 0.0
        self.tracks[track].addControllerEvent(channel,time, 101, controller_msb,   
            insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1
        self.tracks[track].addControllerEvent(channel,time+delta, 100, controller_lsb,  
            insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1 
        self.tracks[track].addControllerEvent(channel,time+(2.0*delta), 6,   data_msb,        
            insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1 
        if data_lsb is not None:
            self.tracks[track].addControllerEvent(channel,time+(3.0*delta), 38, data_lsb, 
                insertion_order = self.event_counter)
            self.event_counter = self.event_counter + 1

    def makeNRPNCall(self, track, channel, time, controller_msb,
                     controller_lsb, data_msb, data_lsb, time_order=False):
        '''

        Perform a Non-Registered Parameter Number Call

        :param track: The track to which this applies 
        :param channel: The channel to which this applies 
        :param time: The time of the event 
        :param controller_msb: The Most significant byte of thecontroller. In common usage
            this will usually be 0
        :param controller_lsb: The least significant byte for the controller message. For example, for
            a fine-tunning change this would be 01.
        :param data_msb: The most significant byte of the controller's parameter.  
        :param data_lsb: The least significant byte of the controller's parameter. If none is needed this
            should be set to ``None``
        :param time_order: Order the control events in time (see below)

        The ``time_order`` parameter is something of a work-around for sequencers that
        do not preserve the order of events from the MIDI files they import. Within this code
        care is taken to preserve the order of events as specified, but some sequencers
        seem to transmit events occurring at the same time in an arbitrary order.
        By setting this parameter to ``True`` something of a work-around is performed: each
        successive event (of which there are three or four for this event type) is placed
        in the time stream a small delta from the preceding one. Thus, for example, the
        controllers are set before the data bytes in this call.

        ''' 
        if self.header.numeric_format == 1:
            track = track + 1
        if time_order:
            delta = 1.0 / (TICKSPERBEAT - 10)
        else:
            delta = 0.0
        self.tracks[track].addControllerEvent(channel,time, 99, controller_msb,
            insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1
        self.tracks[track].addControllerEvent(channel,time+delta, 98, controller_lsb,  
            insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1 
        self.tracks[track].addControllerEvent(channel,time+(2*delta), 6,   data_msb, 
            insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1 
        if data_lsb is not None:
            self.tracks[track].addControllerEvent(channel,time+(3*delta), 38,  data_lsb, 
                insertion_order = self.event_counter)
            self.event_counter = self.event_counter + 1

    def changeTuningBank(self,track, channel, time, bank, time_order=False):
        '''

        Change the tuning bank for a selected track

        :param track: The track to which the data should be written
        :param channel: The channel for the event
        :param time: The time of the event
        :param bank: The tuning bank (0-127)
        :param time_order: Preserve the ordering of the component events by ordering
            in time. See ``makeRPNCall()`` for a discussion of when this may be necessary

        Note that this is a convenience function, as the same
        functionality is available from directly sequencing controller
        events.

        The specified tuning should already have been written to the
        stream with ``changeNoteTuning``.  ''' 
        self.makeRPNCall(track, channel, time, 0, 4, 0, bank, time_order=time_order)

    def changeTuningProgram(self,track, channel, time, program, time_order=False):
        '''

        Change the tuning program for a selected track

        :param track: The track to which the data should be written
        :param channel: The channel for the event
        :param time: The time of the event
        :param program: The tuning program number (0-127)
        :param time_order: Preserve the ordering of the component events by ordering
            in time. See ``makeRPNCall()`` for a discussion of when this may be necessary

        Note that this is a convenience function, as the same
        functionality is available from directly sequencing controller
        events.

        The specified tuning should already have been written to the
        stream with ``changeNoteTuning``.  ''' 
        self.makeRPNCall(track, channel, time, 0, 3, 0, program, time_order=time_order)
        
    def changeNoteTuning(self,  track,  tunings,   sysExChannel=0x7F,  \
                         realTime=True,  tuningProgam=0):
        """        
        Add a real-time MIDI tuning standard update to a track.
        
        :param track: The track to which the tuning is applied.
        :param tunings: A list to tuples representing the tuning. See below for an
            explanation.
        :param sysExChannel: The SysEx channel of the event. This is mapped to "manufacturer ID"
            in the event which is written. Unless there is a specific reason for changing it, it
            should be left at its default value.
        :param realTime: Speicifes if the Universal SysEx event should be flagged as real-time or
            non-real-time. As with the ``sysExChannel`` argument, this should in general
            be left at it's default value.
        :param tuningProgram: The tuning program number.
        
        This function specifically implements the "real time single note tuning
        change" (although the name is misleading, as multiple notes can be included in
        each event). It should be noted that not all hardware or software implements the
        MIDI tuning standard, and that which does often does not implement it in its
        entirety.
        
        The ``tunings`` argument is a list of tuples, in (*note number*, *frequency*) format.
        As an example, if one wanted to change the frequency on MIDI note 69 to 500 (it is normally
        440 Hz), one could do it thus:
        
        .. code:: python
        
            from midiutil.MidiFile import MIDIFile
            MyMIDI = MIDIFile(1)
            tuning = [(69, 500)]
            MyMIDI.changeNoteTuning(0, tuning, tuningProgam=0)
        """
        if self.header.numeric_format == 1:
            track = track + 1
        self.tracks[track].changeNoteTuning(tunings,   sysExChannel,  realTime,\
            tuningProgam, insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1
  


    def addSysEx(self,track, time, manID, payload):
        '''
        
        Add a System Exclusive event.
        
        :param track: The track to which the event should be written
        :param time: The time of the event.
        :param manID: The manufacturer ID for the event
        :param payload: The payload for the event. This should be a binary-packed
            value, and will vary for each type and function.
            
        **Note**: This is a low-level MIDI function, so care must be used in
        constructing the payload. It is recommended that higher-level helper
        functions be written to wrap this function and construct the payload if
        a developer finds him or herself using the function heavily.

        '''
        if self.header.numeric_format == 1:
            track = track + 1
        self.tracks[track].addSysEx(time,manID, payload, insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1
    
    def addUniversalSysEx(self, track, time, code, subcode, payload,  \
                          sysExChannel=0x7F,  realTime=False):
        '''
        
        Add a Univeral System Exclusive event.
        
        :param track: The track to which the event should be written
        :param time: The time of the event, in beats.
        :param code: The event code. [Integer]
        :param subcode: The event sub-code [Integer]
        :param payload: The payload for the event. This should be a binary-packed
            value, and will vary for each type and function.
        :param sysExChannel: The SysEx channel.
        :param realTime: Sets the real-time flag. Defaults to non-real-time.
        :param manID: The manufacturer ID for the event
        
            
        **Note**: This is a low-level MIDI function, so care must be used in
        constructing the payload. It is recommended that higher-level helper
        functions be written to wrap this function and construct the payload if
        a developer finds him or herself using the function heavily. As an example
        of such a helper function, see the ``changeNoteTuning()`` function,
        which uses the event to create a real-time note tuning update.

        '''
        if self.header.numeric_format == 1:
            track = track + 1
        self.tracks[track].addUniversalSysEx(time, code, subcode, payload,  sysExChannel,\
                                               realTime, insertion_order = self.event_counter)
        self.event_counter = self.event_counter + 1

    def writeFile(self,fileHandle):
        '''
        Write the MIDI File.
        
        :param fileHandle: A file handle that has been opened for binary writing.
        '''
        
        self.header.writeFile(fileHandle)
        
        #Close the tracks and have them create the MIDI event data structures.
        self.close()
        
        #Write the MIDI Events to file.
        for i in range(0,self.numTracks):
            self.tracks[i].writeTrack(fileHandle)
                      
    def shiftTracks(self,  offset=0):
        """Shift tracks to be zero-origined, or origined at offset.
        
        Note that the shifting of the time in the tracks uses the MIDIEventList -- in other
        words it is assumed to be called in the stage where the MIDIEventList has been
        created. This function, however, it meant to operate on the eventList itself.
        """
        origin = 1000000 # A little silly, but we'll assume big enough

        for track in self.tracks:
                if len(track.eventList) > 0:
                    for event in track.eventList:
                        if event.time < origin:
                            origin = event.time
        
        for track in self.tracks:
            tempEventList = []
            #runningTime = 0 
        
            for event in track.eventList:
                adjustedTime = event.time - origin
                #event.time = adjustedTime - runningTime + offset
                event.time = adjustedTime + offset
                #runningTime = adjustedTime
                tempEventList.append(event)
            
            track.eventList = tempEventList

    #End Public Functions ########################
    
    def close(self):
        '''
        Close the MIDIFile for further writing.
        
        To close the File for events, we must close the tracks, adjust the time to be
        zero-origined, and have the tracks write to their MIDI Stream data structure.
        '''
        
        if self.closed == True:
            return
                
        for i in range(0,self.numTracks):
            self.tracks[i].closeTrack()
            # We want things like program changes to come before notes when they are at the
            # same time, so we sort the MIDI events by their ordinality
            self.tracks[i].MIDIEventList.sort(key=sort_events)
            
        origin = self.findOrigin()

        for i in range(0,self.numTracks):
            self.tracks[i].adjustTimeAndOrigin(origin, self.adjust_origin)
            self.tracks[i].writeMIDIStream()
            
        self.closed = True
    
    
    def findOrigin(self):
        '''
        Find the earliest time in the file's tracks.append.
        '''
        origin = 1000000 # A little silly, but we'll assume big enough

    # Note: This code assumes that the MIDIEventList has been sorted, so this should be insured
    # before it is called. It is probably a poor design to do this. 
    # TODO: -- Consider making this less efficient but more robust by not assuming the list to be sorted.
    
        for track in self.tracks:
                if len(track.MIDIEventList) > 0:
                    if track.MIDIEventList[0].time < origin:
                        origin = track.MIDIEventList[0].time
                        
        
        return origin
            
def writeVarLength(i):
    '''
    Accept an input, and write a MIDI-compatible variable length stream
    
    The MIDI format is a little strange, and makes use of so-called variable
    length quantities. These quantities are a stream of bytes. If the most
    significant bit is 1, then more bytes follow. If it is zero, then the
    byte in question is the last in the stream
    '''
    input = int(i+0.5)
    output = [0,0,0,0]
    reversed = [0,0,0,0]
    count = 0
    result = input & 0x7F
    output[count] = result
    count = count + 1
    input = input >> 7
    while input > 0:
        result = input & 0x7F 
        result = result | 0x80
        output[count] = result
        count = count + 1
        input = input >> 7  

    reversed[0] = output[3]
    reversed[1] = output[2]
    reversed[2] = output[1]
    reversed[3] = output[0]
    return reversed[4-count:4]

# readVarLength is taken from the MidiFile class.

def readVarLength(offset, buffer):
    '''
    A function to read a MIDI variable length variable.

    It returns a tuple of the value read and the number of bytes processed. The
    input is an offset into the buffer, and the buffer itself.
    '''
    toffset = offset
    output = 0
    bytesRead = 0
    while True:
        output = output << 7
        byte = struct.unpack_from('>B',buffer,toffset)[0]
        toffset = toffset + 1
        bytesRead = bytesRead + 1
        output = output + (byte & 127)
        if (byte & 128) == 0:
            break
    return (output, bytesRead)

def frequencyTransform(freq):
    '''
    Returns a three-byte transform of a frequency.
    '''
    resolution = 16384
    freq = float(freq)
    dollars = 69 + 12 * math.log(freq/(float(440)), 2)
    firstByte = int(dollars)
    lowerFreq = 440 * pow(2.0, ((float(firstByte) - 69.0)/12.0))
    if freq != lowerFreq:
        centDif = 1200 * math.log( (freq/lowerFreq), 2)
    else:
        centDif = 0
    cents = round(centDif/100 * resolution) # round?
    secondByte = min([int(cents)>>7, 0x7F])
    thirdByte = cents - (secondByte << 7)
    thirdByte = min([thirdByte, 0x7f])
    if thirdByte == 0x7f and secondByte == 0x7F and firstByte == 0x7F:
        thirdByte = 0x7e
        
    thirdByte = int(thirdByte)
    return [firstByte,  secondByte,  thirdByte]
    
def returnFrequency(freqBytes):
    '''The reverse of frequencyTransform. Given a byte stream, return a frequency.
    '''
    resolution = 16384.0
    baseFrequency = 440 * pow(2.0, (float(freqBytes[0]-69.0)/12.0))
    frac = (float((int(freqBytes[1]) << 7) + int(freqBytes[2])) * 100.0) / resolution
    frequency = baseFrequency * pow(2.0, frac/1200.0)
    return frequency
    
def sort_events(event):
    '''
    .. py:function:: sort_events(event)
    
        The key function used to sort events (both MIDI and Generic)
        
        :param event: An object of type :class:`MIDIEvent` or (a derrivative of)
            :class:`GenericEvent`
        
        This function should be provided as the ``key`` for both ``list.sort()``
        and ``sorted()``. By using it sorting will be as follows:
        
        * Events are ordered in time. An event that takes place earlier will
          appear earlier
        * If two events happen at the same time, the secondary sort key is
          ``ord``. Thus a class of events can be processed earlier than another.
          One place this is used in the code is to make sure that note off events
          are processed before note on events.
        * If time and ordinality are the same, they are sorted in the order in which
          they were originally added to the list. Thus, for example, if one is making
          an RPN call one can specify the controller change events in the proper order
          and be sure that they will end up in the file that way.
    '''
    
    return (event.time, event.ord, event.insertion_order)
