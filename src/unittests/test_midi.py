#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Name:        miditest.py
# Purpose:     Unit testing harness for midiutil
#
# Author:      Mark Conway Wirt <emergentmusics) at (gmail . com>
#
# Created:     2008/04/17
# Copyright:   (c) 2009-2016, Mark Conway Wirt
# License:     Please see License.txt for the terms under which this
#              software is distributed.
# -----------------------------------------------------------------------------


from __future__ import division, print_function
import sys
import struct

import unittest

from midiutil.MidiFile import *

from midiutil.MidiFile import writeVarLength,  \
    frequencyTransform, returnFrequency, MAJOR, MINOR, SHARPS, FLATS, MIDIFile


class Decoder(object):
    '''
    An immutable comtainer for MIDI data. This is needed bcause if one indexes
    into a byte string in Python 3 one gets an ``int`` as a return.
    '''
    def __init__(self, data):
        self.data = data.decode("ISO-8859-1")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key].encode("ISO-8859-1")

    def unpack_into_byte(self, key):
        return struct.unpack('>B', self[key])[0]


class TestMIDIUtils(unittest.TestCase):

    def testWriteVarLength(self):
        self.assertEqual(writeVarLength(0x70), [0x70])
        self.assertEqual(writeVarLength(0x80), [0x81, 0x00])
        self.assertEqual(writeVarLength(0x1FFFFF), [0xFF, 0xFF, 0x7F])
        self.assertEqual(writeVarLength(0x08000000), [0xC0, 0x80, 0x80, 0x00])

    def testAddNote(self):
        MyMIDI = MIDIFile(1)  # a format 1 file, so we increment the track number below
        track = 0
        channel = 0
        pitch = 100
        time = 0
        duration = 1
        volume = 100
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        self.assertEqual(MyMIDI.tracks[1].eventList[0].evtname, "NoteOn")
        self.assertEqual(MyMIDI.tracks[1].eventList[0].pitch, pitch)
        self.assertEqual(MyMIDI.tracks[1].eventList[0].tick, MyMIDI.time_to_ticks(time))
        self.assertEqual(MyMIDI.tracks[1].eventList[0].duration, MyMIDI.time_to_ticks(duration))
        self.assertEqual(MyMIDI.tracks[1].eventList[0].volume, volume)

    def testShiftTrack(self):
        track = 0
        channel = 0
        pitch = 100
        time = 1
        duration = 1
        volume = 100
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        self.assertEqual(MyMIDI.tracks[1].eventList[0].evtname, "NoteOn")
        self.assertEqual(MyMIDI.tracks[1].eventList[0].pitch, pitch)
        self.assertEqual(MyMIDI.tracks[1].eventList[0].tick, MyMIDI.time_to_ticks(time))
        self.assertEqual(MyMIDI.tracks[1].eventList[0].duration, MyMIDI.time_to_ticks(duration))
        self.assertEqual(MyMIDI.tracks[1].eventList[0].volume, volume)
        MyMIDI.shiftTracks()
        self.assertEqual(MyMIDI.tracks[1].eventList[0].tick, 0)

    def testDeinterleaveNotes(self):
        MyMIDI = MIDIFile(1, adjust_origin=False)
        track = 0
        channel = 0
        pitch = 100
        time1 = 0
        time2 = 1
        duration = 2
        volume = 100
        MyMIDI.addNote(track, channel, pitch, time1, duration, volume)  # on at 0 off at 2
        MyMIDI.addNote(track, channel, pitch, time2, duration, volume + 1)  # on at 1 off at 3
        MyMIDI.close()

        # ticks have already been converted to delta ticks
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].tick, MyMIDI.time_to_ticks(time1))
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].evtname, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].tick, MyMIDI.time_to_ticks(time2))
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[2].evtname, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[2].tick, MyMIDI.time_to_ticks(time2 - time2))
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[3].evtname, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[3].tick, MyMIDI.time_to_ticks(time2 - time2 + duration))

    def testTimeShift(self):

        # With one track
        MyMIDI = MIDIFile(1, adjust_origin=True)
        track = 0
        channel = 0
        pitch = 100
        time1 = 5
        duration = 1
        volume = 100
        MyMIDI.addNote(track, channel, pitch, time1, duration, volume)
        MyMIDI.close()
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].tick, MyMIDI.time_to_ticks(0))
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].evtname, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].tick, MyMIDI.time_to_ticks(duration))

        # With two tracks
        track2 = 1
        MyMIDI = MIDIFile(2, adjust_origin=True)
        MyMIDI.addNote(track, channel, pitch, time1, duration, volume)
        time2 = 6
        MyMIDI.addNote(track2, channel, pitch, time2, duration, volume)
        MyMIDI.close()
        # ticks have already been converted to delta ticks
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].tick, MyMIDI.time_to_ticks(0))
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].evtname, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].tick, MyMIDI.time_to_ticks(duration))
        self.assertEqual(MyMIDI.tracks[2].MIDIEventList[0].evtname, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[2].MIDIEventList[0].tick, MyMIDI.time_to_ticks(0 + duration))
        self.assertEqual(MyMIDI.tracks[2].MIDIEventList[1].evtname, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[2].MIDIEventList[1].tick, MyMIDI.time_to_ticks(0 + duration))

        # Negative Time
        MyMIDI = MIDIFile(1, adjust_origin=True)
        track = 0
        channel = 0
        pitch = 100
        time = -5
        duration = 1
        volume = 100
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        MyMIDI.close()
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].tick, MyMIDI.time_to_ticks(0))
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].evtname, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].tick, MyMIDI.time_to_ticks(0 + duration))

        # Negative time, two tracks

        MyMIDI = MIDIFile(2, adjust_origin=True)
        track = 0
        channel = 0
        pitch = 100
        time = -1
        duration = 1
        volume = 100
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        track2 = 1
        time2 = 0
        MyMIDI.addNote(track2, channel, pitch, time2, duration, volume)
        MyMIDI.close()
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].tick, MyMIDI.time_to_ticks(0))
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].evtname, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].tick, MyMIDI.time_to_ticks(1))
        self.assertEqual(MyMIDI.tracks[2].MIDIEventList[0].evtname, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[2].MIDIEventList[0].tick, MyMIDI.time_to_ticks(1))
        self.assertEqual(MyMIDI.tracks[2].MIDIEventList[1].evtname, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[2].MIDIEventList[1].tick, MyMIDI.time_to_ticks(1))

    def testFrequency(self):
        freq = frequencyTransform(8.1758)
        self.assertEqual(freq[0], 0x00)
        self.assertEqual(freq[1], 0x00)
        self.assertEqual(freq[2], 0x00)
        freq = frequencyTransform(8.66196)  # 8.6620 in MIDI documentation
        self.assertEqual(freq[0], 0x01)
        self.assertEqual(freq[1], 0x00)
        self.assertEqual(freq[2], 0x00)
        freq = frequencyTransform(440.00)
        self.assertEqual(freq[0], 0x45)
        self.assertEqual(freq[1], 0x00)
        self.assertEqual(freq[2], 0x00)
        freq = frequencyTransform(440.0016)
        self.assertEqual(freq[0], 0x45)
        self.assertEqual(freq[1], 0x00)
        self.assertEqual(freq[2], 0x01)
        freq = frequencyTransform(439.9984)
        self.assertEqual(freq[0], 0x44)
        self.assertEqual(freq[1], 0x7f)
        self.assertEqual(freq[2], 0x7f)
        freq = frequencyTransform(8372.0190)
        self.assertEqual(freq[0], 0x78)
        self.assertEqual(freq[1], 0x00)
        self.assertEqual(freq[2], 0x00)
        freq = frequencyTransform(8372.062)  # 8372.0630 in MIDI documentation
        self.assertEqual(freq[0], 0x78)
        self.assertEqual(freq[1], 0x00)
        self.assertEqual(freq[2], 0x01)
        freq = frequencyTransform(13289.7300)
        self.assertEqual(freq[0], 0x7F)
        self.assertEqual(freq[1], 0x7F)
        self.assertEqual(freq[2], 0x7E)
        freq = frequencyTransform(12543.8760)
        self.assertEqual(freq[0], 0x7F)
        self.assertEqual(freq[1], 0x00)
        self.assertEqual(freq[2], 0x00)
        freq = frequencyTransform(8.2104)  # Just plain wrong in documentation, as far as I can tell.
        # self.assertEqual(freq[0],  0x0)
        # self.assertEqual(freq[1],  0x0)
        # self.assertEqual(freq[2],  0x1)

        # Test the inverse
        testFreq = 15.0
        accuracy = 0.00001
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy * testFreq), True)
        testFreq = 200.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy * testFreq), True)
        testFreq = 400.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy * testFreq), True)
        testFreq = 440.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy * testFreq), True)
        testFreq = 1200.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy * testFreq), True)
        testFreq = 5000.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy * testFreq), True)
        testFreq = 12000.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy * testFreq), True)

    def testSysEx(self):
        MyMIDI = MIDIFile(1)
        MyMIDI.addSysEx(0, 0, 0, struct.pack('>B', 0x01))
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'SysEx')

        self.assertEqual(data.unpack_into_byte(0), 0x00)
        self.assertEqual(data.unpack_into_byte(1), 0xf0)
        self.assertEqual(data.unpack_into_byte(2), 3)
        self.assertEqual(data.unpack_into_byte(3), 0x00)
        self.assertEqual(data.unpack_into_byte(4), 0x01)
        self.assertEqual(data.unpack_into_byte(5), 0xf7)

    def testPitchWheel(self):

        val = 1000
        MyMIDI = MIDIFile(1)
        MyMIDI.addPitchWheelEvent(0, 0, 0, val)
        MyMIDI.close()

        MSB = (val + 8192) >> 7
        LSB = (val + 8192) & 0x7F

        data = Decoder(MyMIDI.tracks[1].MIDIdata)
        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 224)   # Code
        self.assertEqual(data.unpack_into_byte(2), LSB)
        self.assertEqual(data.unpack_into_byte(3), MSB)

        val = -1000
        MyMIDI = MIDIFile(1)
        MyMIDI.addPitchWheelEvent(0, 0, 0, val)
        MyMIDI.close()

        MSB = (val + 8192) >> 7
        LSB = (val + 8192) & 0x7F

        data = Decoder(MyMIDI.tracks[1].MIDIdata)
        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 224)   # Code
        self.assertEqual(data.unpack_into_byte(2), LSB)
        self.assertEqual(data.unpack_into_byte(3), MSB)

    def testTempo(self):
        tempo = 60
        MyMIDI = MIDIFile(1, file_format=2)
        MyMIDI.addTempo(0, 0, tempo)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[0].MIDIdata)

        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].evtname, 'Tempo')

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xff)  # Code
        self.assertEqual(data.unpack_into_byte(2), 0x51)
        self.assertEqual(data.unpack_into_byte(3), 0x03)
        self.assertEqual(data[4:7], struct.pack('>L', int(60000000 / tempo))[1:4])

        # Also check the format 1 file

        tempo = 60
        MyMIDI = MIDIFile(2, file_format=1)
        MyMIDI.addTempo(1, 0, tempo)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[0].MIDIdata)

        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].evtname, 'Tempo')

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xff)  # Code
        self.assertEqual(data.unpack_into_byte(2), 0x51)
        self.assertEqual(data.unpack_into_byte(3), 0x03)
        self.assertEqual(data[4:7], struct.pack('>L', int(60000000 / tempo))[1:4])

    def testCopyright(self):
        notice = "2016(C) MCW"
        MyMIDI = MIDIFile(1)
        MyMIDI.addCopyright(0, 0, notice)
        MyMIDI.close()

        payload_encoded = notice.encode("ISO-8859-1")
        payloadLength = len(payload_encoded)
        payloadLengthVar = writeVarLength(payloadLength)

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'Copyright')

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xff)  # Code
        self.assertEqual(data.unpack_into_byte(2), 0x02)  # Subcode
        index = 3
        for i in range(len(payloadLengthVar)):
            self.assertEqual(data.unpack_into_byte(index), payloadLengthVar[i])
            index = index + 1
        for i in range(len(payload_encoded)):
            if sys.version_info < (3,):
                test_char = ord(payload_encoded[i])
            else:
                test_char = payload_encoded[i]
            self.assertEqual(data.unpack_into_byte(index), test_char)
            index = index + 1

    def testText(self):
        text = "2016(C) MCW"
        MyMIDI = MIDIFile(1)
        MyMIDI.addText(0, 0, text)
        MyMIDI.close()

        payload_encoded = text.encode("ISO-8859-1")
        payloadLength = len(payload_encoded)
        payloadLengthVar = writeVarLength(payloadLength)

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'Text')

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xff)  # Code
        self.assertEqual(data.unpack_into_byte(2), 0x01)  # Subcode
        index = 3
        for i in range(len(payloadLengthVar)):
            self.assertEqual(data.unpack_into_byte(index), payloadLengthVar[i])
            index = index + 1
        for i in range(len(payload_encoded)):
            if sys.version_info < (3,):
                test_char = ord(payload_encoded[i])
            else:
                test_char = payload_encoded[i]
            self.assertEqual(data.unpack_into_byte(index), test_char)
            index = index + 1

    def testTimeSignature(self):
        time = 0
        track = 0
        numerator = 4
        denominator = 2
        clocks_per_tick = 24
        MyMIDI = MIDIFile(1, file_format=2)
        MyMIDI.addTimeSignature(track, time, numerator, denominator, clocks_per_tick)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[0].MIDIdata)

        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].evtname, 'TimeSignature')

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xFF)  # Code
        self.assertEqual(data.unpack_into_byte(2), 0x58)  # subcode
        self.assertEqual(data.unpack_into_byte(3), 0x04)  # Data length
        self.assertEqual(data.unpack_into_byte(4), numerator)
        self.assertEqual(data.unpack_into_byte(5), denominator)
        self.assertEqual(data.unpack_into_byte(6), clocks_per_tick)  # Data length
        self.assertEqual(data.unpack_into_byte(7), 0x08)  # 32nd notes per quarter note

        # We also want to check with a format 1 file, make sure it ends up in
        # the tempo track

        time = 0
        track = 1
        numerator = 4
        denominator = 2
        clocks_per_tick = 24
        MyMIDI = MIDIFile(2, file_format=1)
        MyMIDI.addTimeSignature(track, time, numerator, denominator, clocks_per_tick)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[0].MIDIdata)

        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].evtname, 'TimeSignature')

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xFF)  # Code
        self.assertEqual(data.unpack_into_byte(2), 0x58)  # subcode
        self.assertEqual(data.unpack_into_byte(3), 0x04)  # Data length
        self.assertEqual(data.unpack_into_byte(4), numerator)
        self.assertEqual(data.unpack_into_byte(5), denominator)
        self.assertEqual(data.unpack_into_byte(6), clocks_per_tick)  # Data length
        self.assertEqual(data.unpack_into_byte(7), 0x08)  # 32nd notes per quarter note

    def testKeySignature(self):
        time            = 0
        track           = 0
        accidentals     = 3
        accidental_type = MINOR
        mode            = MAJOR

        MyMIDI = MIDIFile(1)
        MyMIDI.addKeySignature(track, time, accidentals, accidental_type, mode)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[0].MIDIdata)

        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].evtname, 'KeySignature')

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xFF)  # Code
        self.assertEqual(data.unpack_into_byte(2), 0x59)  # subcode
        self.assertEqual(data.unpack_into_byte(3), 0x02)  # Event subtype
        self.assertEqual(data.unpack_into_byte(4), accidentals * accidental_type)
        self.assertEqual(data.unpack_into_byte(5), mode)

    def testProgramChange(self):
        program = 10
        channel = 0
        tracknum = 0
        realtracknum = tracknum
        time = 0.0
        MyMIDI = MIDIFile(1)
        if MyMIDI.header.numeric_format == 1:
            realtracknum = tracknum + 1
        MyMIDI.addProgramChange(tracknum, channel, time, program)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[realtracknum].MIDIdata)

        self.assertEqual(MyMIDI.tracks[realtracknum].MIDIEventList[0].evtname, 'ProgramChange')
        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xC << 4 | channel)  # Code
        self.assertEqual(data.unpack_into_byte(2), program)

    def testChannelPressure(self):
        pressure = 10
        channel = 0
        time = 0.0
        tracknum = 0
        realtracknum = tracknum
        MyMIDI = MIDIFile(1)
        if MyMIDI.header.numeric_format == 1:
            realtracknum = tracknum + 1
        MyMIDI.addChannelPressure(tracknum, channel, time, pressure)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[realtracknum].MIDIdata)

        self.assertEqual(MyMIDI.tracks[realtracknum].MIDIEventList[0].evtname, 'ChannelPressure')
        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xD0 | channel)  # Code
        self.assertEqual(data.unpack_into_byte(2), pressure)

    def testTrackName(self):
        track_name = "track"
        MyMIDI = MIDIFile(1)
        MyMIDI.addTrackName(0, 0, track_name)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'TrackName')

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xFF)  # Code
        self.assertEqual(data.unpack_into_byte(2), 0x03)  # subcodes

    def testLongTrackName(self):
        track_name = 'long track name ' * 8
        MyMIDI = MIDIFile(1)
        MyMIDI.addTrackName(0, 0, track_name)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'TrackName')

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xFF)  # Code
        self.assertEqual(data.unpack_into_byte(2), 0x03)  # subcodes

    def testTuningBank(self):
        bank = 1
        channel = 0
        MyMIDI = MIDIFile(1)
        MyMIDI.changeTuningBank(0, 0, 0, bank)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'ControllerEvent')

        self.assertEqual(data.unpack_into_byte(0), 0x00)                # time
        self.assertEqual(data.unpack_into_byte(1), 0xB << 4 | channel)  # Code
        self.assertEqual(data.unpack_into_byte(2), 0x65)                # Controller Number
        self.assertEqual(data.unpack_into_byte(3), 0x0)                 # Controller Value
        self.assertEqual(data.unpack_into_byte(4), 0x00)                # time
        self.assertEqual(data.unpack_into_byte(5), 0xB << 4 | channel)  # Code
        self.assertEqual(data.unpack_into_byte(6), 0x64)                # Controller Number
        self.assertEqual(data.unpack_into_byte(7), 0x4)                 # Controller Value
        self.assertEqual(data.unpack_into_byte(8), 0x00)                # time
        self.assertEqual(data.unpack_into_byte(9), 0xB << 4 | channel)  # Code
        self.assertEqual(data.unpack_into_byte(10), 0x06)               # Bank MSB
        self.assertEqual(data.unpack_into_byte(11), 0x00)               # Value
        self.assertEqual(data.unpack_into_byte(12), 0x00)               # time
        self.assertEqual(data.unpack_into_byte(13), 0xB << 4 | channel)  # Code
        self.assertEqual(data.unpack_into_byte(14), 0x26)                # Bank LSB
        self.assertEqual(data.unpack_into_byte(15), bank)                # Bank value (bank number)

    def testTuningBankWithTimeOrder(self):
        bank = 1
        MyMIDI = MIDIFile(1)
        MyMIDI.changeTuningBank(0, 0, 0, bank, time_order=True)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'ControllerEvent')

        self.assertEqual(data.unpack_into_byte(0), 0x00)               # time
        self.assertEqual(data.unpack_into_byte(4), 0x01)               # time
        self.assertEqual(data.unpack_into_byte(8), 0x01)               # time
        self.assertEqual(data.unpack_into_byte(12), 0x01)               # time

    def testTuningProgram(self):
        program = 10
        channel = 0
        MyMIDI = MIDIFile(1)
        MyMIDI.changeTuningProgram(0, 0, 0, program)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'ControllerEvent')

        self.assertEqual(data.unpack_into_byte(0), 0x00)                 # time
        self.assertEqual(data.unpack_into_byte(1), 0xB << 4 | channel)   # Code
        self.assertEqual(data.unpack_into_byte(2), 0x65)                 # Controller Number
        self.assertEqual(data.unpack_into_byte(3), 0x0)                  # Controller Value
        self.assertEqual(data.unpack_into_byte(4), 0x00)                 # time
        self.assertEqual(data.unpack_into_byte(5), 0xB << 4 | channel)   # Code
        self.assertEqual(data.unpack_into_byte(6), 0x64)                 # Controller Number
        self.assertEqual(data.unpack_into_byte(7), 0x03)                 # Controller Value
        self.assertEqual(data.unpack_into_byte(8), 0x00)                 # time
        self.assertEqual(data.unpack_into_byte(9), 0xB << 4 | channel)   # Code
        self.assertEqual(data.unpack_into_byte(10), 0x06)                # Bank MSB
        self.assertEqual(data.unpack_into_byte(11), 0x00)                # Value
        self.assertEqual(data.unpack_into_byte(12), 0x00)                # time
        self.assertEqual(data.unpack_into_byte(13), 0xB << 4 | channel)  # Code
        self.assertEqual(data.unpack_into_byte(14), 0x26)                # Bank LSB
        self.assertEqual(data.unpack_into_byte(15), program)             # Bank value (bank number)

    def testTuningProgramWithTimeOrder(self):
        program = 10
        MyMIDI = MIDIFile(1)
        MyMIDI.changeTuningProgram(0, 0, 0, program, time_order=True)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'ControllerEvent')

        self.assertEqual(data.unpack_into_byte(0), 0x00)              # time
        self.assertEqual(data.unpack_into_byte(4), 0x01)              # time
        self.assertEqual(data.unpack_into_byte(8), 0x01)              # time
        self.assertEqual(data.unpack_into_byte(12), 0x01)             # time

    def testNRPNCall(self):
        track          = 0
        time           = 0
        channel        = 0
        controller_msb = 1
        controller_lsb = 2
        data_msb       = 3
        data_lsb       = 4
        MyMIDI = MIDIFile(1)
        MyMIDI.makeNRPNCall(track, channel, time, controller_msb, controller_lsb, data_msb, data_lsb)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'ControllerEvent')

        self.assertEqual(data.unpack_into_byte(0), 0x00)                 # time
        self.assertEqual(data.unpack_into_byte(1), 0xB << 4 | channel)   # Code
        self.assertEqual(data.unpack_into_byte(2), 99)                   # Controller Number
        self.assertEqual(data.unpack_into_byte(3), controller_msb)       # Controller Value
        self.assertEqual(data.unpack_into_byte(4), 0x00)                 # time
        self.assertEqual(data.unpack_into_byte(5), 0xB << 4 | channel)   # Code
        self.assertEqual(data.unpack_into_byte(6), 98)                   # Controller Number
        self.assertEqual(data.unpack_into_byte(7), controller_lsb)       # Controller Value
        self.assertEqual(data.unpack_into_byte(8), 0x00)                 # time
        self.assertEqual(data.unpack_into_byte(9), 0xB << 4 | channel)   # Code
        self.assertEqual(data.unpack_into_byte(10), 0x06)                # Bank MSB
        self.assertEqual(data.unpack_into_byte(11), data_msb)            # Value
        self.assertEqual(data.unpack_into_byte(12), 0x00)                # time
        self.assertEqual(data.unpack_into_byte(13), 0xB << 4 | channel)  # Code
        self.assertEqual(data.unpack_into_byte(14), 0x26)                # Bank LSB
        self.assertEqual(data.unpack_into_byte(15), data_lsb)  # Bank value (bank number)

    def testNRPNCallWithTimeOrder(self):
        track          = 0
        time           = 0
        channel        = 0
        controller_msb = 1
        controller_lsb = 2
        data_msb       = 3
        data_lsb       = 4
        MyMIDI = MIDIFile(1)
        MyMIDI.makeNRPNCall(track, channel, time, controller_msb, controller_lsb, data_msb, data_lsb, time_order=True)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'ControllerEvent')

        self.assertEqual(data.unpack_into_byte(0), 0x00)                 # time
        self.assertEqual(data.unpack_into_byte(1), 0xB << 4 | channel)   # Code
        self.assertEqual(data.unpack_into_byte(2), 99)                   # Controller Number
        self.assertEqual(data.unpack_into_byte(3), controller_msb)       # Controller Value
        self.assertEqual(data.unpack_into_byte(4), 0x01)                 # time
        self.assertEqual(data.unpack_into_byte(5), 0xB << 4 | channel)   # Code
        self.assertEqual(data.unpack_into_byte(6), 98)                   # Controller Number
        self.assertEqual(data.unpack_into_byte(7), controller_lsb)       # Controller Value
        self.assertEqual(data.unpack_into_byte(8), 0x01)                 # time
        self.assertEqual(data.unpack_into_byte(9), 0xB << 4 | channel)   # Code
        self.assertEqual(data.unpack_into_byte(10), 0x06)                # Bank MSB
        self.assertEqual(data.unpack_into_byte(11), data_msb)            # Value
        self.assertEqual(data.unpack_into_byte(12), 0x01)                # time
        self.assertEqual(data.unpack_into_byte(13), 0xB << 4 | channel)  # Code
        self.assertEqual(data.unpack_into_byte(14), 0x26)                # Bank LSB
        self.assertEqual(data.unpack_into_byte(15), data_lsb)  # Bank value (bank number)

    def testAddControllerEvent(self):
        track = 0
        time = 0
        channel = 3
        controller_number = 1
        parameter = 2
        MyMIDI = MIDIFile(1)
        MyMIDI.addControllerEvent(track, channel, time, controller_number, parameter)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'ControllerEvent')

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # time
        self.assertEqual(data.unpack_into_byte(1), 0xB << 4 | channel)  # Code
        self.assertEqual(data.unpack_into_byte(2), controller_number)  # Controller Number
        self.assertEqual(data.unpack_into_byte(3), parameter)  # Controller Value

    def testNonRealTimeUniversalSysEx(self):
        code           = 1
        subcode        = 2
        payload_number = 42

        payload = struct.pack('>B', payload_number)

        MyMIDI = MIDIFile(1, adjust_origin=False)

        # Just for fun we'll use a multi-byte time
        time = 1
        time_bytes = writeVarLength(time * MyMIDI.ticks_per_quarternote)
        MyMIDI.addUniversalSysEx(0, time, code, subcode, payload, realTime=False)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'UniversalSysEx')

        self.assertEqual(data.unpack_into_byte(0), time_bytes[0])  # Time
        self.assertEqual(data.unpack_into_byte(1), time_bytes[1])  # Time
        self.assertEqual(data.unpack_into_byte(2), 0xf0)  # UniversalSysEx == 0xF0
        self.assertEqual(data.unpack_into_byte(3), 5 + len(payload))    # Payload length = 5+actual pyayload
        self.assertEqual(data.unpack_into_byte(4), 0x7E)  # 0x7E == non-realtime
        self.assertEqual(data.unpack_into_byte(5), 0x7F)  # Sysex channel (always 0x7F)
        self.assertEqual(data.unpack_into_byte(6), code)
        self.assertEqual(data.unpack_into_byte(7), subcode)
        self.assertEqual(data.unpack_into_byte(8), payload_number)  # Data
        self.assertEqual(data.unpack_into_byte(9), 0xf7)  # End of message

    def testRealTimeUniversalSysEx(self):
        code           = 1
        subcode        = 2
        payload_number = 47

        payload = struct.pack('>B', payload_number)
        MyMIDI = MIDIFile(1)
        MyMIDI.addUniversalSysEx(0, 0, code, subcode, payload, realTime=True)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'UniversalSysEx')

        self.assertEqual(data.unpack_into_byte(0), 0x00)
        self.assertEqual(data.unpack_into_byte(1), 0xf0)
        self.assertEqual(data.unpack_into_byte(2), 5 + len(payload))
        self.assertEqual(data.unpack_into_byte(3), 0x7F)  # 0x7F == real-time
        self.assertEqual(data.unpack_into_byte(4), 0x7F)
        self.assertEqual(data.unpack_into_byte(5), code)
        self.assertEqual(data.unpack_into_byte(6), subcode)
        self.assertEqual(data.unpack_into_byte(7), payload_number)
        self.assertEqual(data.unpack_into_byte(8), 0xf7)

    def testTuning(self):
        MyMIDI = MIDIFile(1)
        MyMIDI.changeNoteTuning(0, [(1, 440), (2, 880)])
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].evtname, 'UniversalSysEx')

        self.assertEqual(data.unpack_into_byte(0), 0x00)
        self.assertEqual(data.unpack_into_byte(1), 0xf0)
        self.assertEqual(data.unpack_into_byte(2), 15)
        self.assertEqual(data.unpack_into_byte(3), 0x7F)
        self.assertEqual(data.unpack_into_byte(4), 0x7F)
        self.assertEqual(data.unpack_into_byte(5), 0x08)
        self.assertEqual(data.unpack_into_byte(6), 0x02)
        self.assertEqual(data.unpack_into_byte(7), 0x00)
        self.assertEqual(data.unpack_into_byte(8), 0x2)
        self.assertEqual(data.unpack_into_byte(9), 0x1)
        self.assertEqual(data.unpack_into_byte(10), 69)
        self.assertEqual(data.unpack_into_byte(11), 0)
        self.assertEqual(data.unpack_into_byte(12), 0)
        self.assertEqual(data.unpack_into_byte(13), 0x2)
        self.assertEqual(data.unpack_into_byte(14), 81)
        self.assertEqual(data.unpack_into_byte(15), 0)
        self.assertEqual(data.unpack_into_byte(16), 0)
        self.assertEqual(data.unpack_into_byte(17), 0xf7)

    def testWriteFile(self):
        # Just to make sure the stream can be written without throwing an error.
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(0, 0, 100, 0, 1, 100)
        with open("/tmp/test.mid", "wb") as output_file:
            MyMIDI.writeFile(output_file)

    def testAdjustOrigin(self):
        track    = 0
        channel  = 0
        pitch    = 69
        time     = 1
        duration = 0.1
        volume   = 64
        MyMIDI = MIDIFile(1, adjust_origin=True)
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        time = 1.1
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)

        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(data.unpack_into_byte(0), 0x00)  # first time
        self.assertEqual(data.unpack_into_byte(8), 0x00)  # seconds time

        MyMIDI = MIDIFile(1, adjust_origin=False)
        time = 0.1
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        time = 0.2
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[1].MIDIdata)

        self.assertEqual(data.unpack_into_byte(0), MyMIDI.ticks_per_quarternote / 10)  # first time, should be an integer < 127
        self.assertEqual(data.unpack_into_byte(8), 0x00)  # first time

    def testMultiClose(self):
        track    = 0
        channel  = 0
        pitch    = 69
        time     = 0
        duration = 1.0
        volume   = 64
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        MyMIDI.close()
        data_length_1 = len(MyMIDI.tracks[0].MIDIdata)
        MyMIDI.close()
        data_length_2 = len(MyMIDI.tracks[0].MIDIdata)

        self.assertEqual(data_length_1, data_length_2)
        MyMIDI.tracks[0].closeTrack()
        data_length_3 = len(MyMIDI.tracks[0].MIDIdata)
        self.assertEqual(data_length_1, data_length_3)

    def testEmptyEventList(self):
        MyMIDI = MIDIFile(1)
        MyMIDI.close()
        data_length = len(MyMIDI.tracks[0].MIDIdata)
        self.assertEqual(data_length, 4)  # Header length  4

    def testRemoveDuplicates(self):
        # First notes
        track    = 0
        channel  = 0
        pitch    = 69
        time     = 0
        duration = 1
        volume   = 64
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)  # also adds a corresponding NoteOff
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)  # also adds a corresponding NoteOff
        MyMIDI.close()
        self.assertEqual(2, len(MyMIDI.tracks[1].eventList))  # One NoteOn event, one NoteOff event
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        pitch = 70
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        MyMIDI.close()
        self.assertEqual(4, len(MyMIDI.tracks[1].eventList))  # Two NoteOn events, two NoteOff events

        # Next tempo
        tempo = 60
        track = 0
        time = 0
        MyMIDI = MIDIFile(1)
        MyMIDI.addTempo(track, time, tempo)
        MyMIDI.addTempo(track, time, tempo)
        MyMIDI.close()
        self.assertEqual(1, len(MyMIDI.tracks[0].eventList))
        MyMIDI = MIDIFile(1)
        MyMIDI.addTempo(track, time, tempo)
        tempo = 80
        MyMIDI.addTempo(track, time, tempo)
        MyMIDI.close()
        self.assertEqual(2, len(MyMIDI.tracks[0].eventList))

        # Program Number
        time = 0
        track = 0
        program = 10
        channel = 0
        MyMIDI = MIDIFile(1)
        MyMIDI.addProgramChange(track, channel, time, program)
        MyMIDI.addProgramChange(track, channel, time, program)
        MyMIDI.close()
        self.assertEqual(1, len(MyMIDI.tracks[track + 1].eventList))
        MyMIDI = MIDIFile(1)
        MyMIDI.addProgramChange(track, channel, time, program)
        program = 11
        MyMIDI.addProgramChange(track, channel, time, program)
        MyMIDI.close()
        self.assertEqual(2, len(MyMIDI.tracks[track + 1].eventList))

        # Track Name
        track = 0
        time = 0
        track_name = "track"
        MyMIDI = MIDIFile(1)
        MyMIDI.addTrackName(track, time, track_name)
        MyMIDI.addTrackName(track, time, track_name)
        MyMIDI.close()
        self.assertEqual(1, len(MyMIDI.tracks[1].eventList))
        MyMIDI = MIDIFile(1)
        MyMIDI.addTrackName(track, time, track_name)
        track_name = "track 2"
        MyMIDI.addTrackName(track, time, track_name)
        MyMIDI.close()
        self.assertEqual(2, len(MyMIDI.tracks[1].eventList))

        # SysEx. These are never removed
        track = 0
        time = 0
        manufacturer = 10
        MyMIDI = MIDIFile(1)
        MyMIDI.addSysEx(track, time, manufacturer, struct.pack('>B', 0x01))
        MyMIDI.addSysEx(track, time, manufacturer, struct.pack('>B', 0x01))
        MyMIDI.close()
        self.assertEqual(2, len(MyMIDI.tracks[1].eventList))

        # UniversalSysEx. Same thing -- never remove

        track          = 0
        time           = 0
        code           = 1
        subcode        = 2
        payload_number = 47

        payload = struct.pack('>B', payload_number)
        MyMIDI = MIDIFile(1)
        MyMIDI.addUniversalSysEx(track, time, code, subcode, payload, realTime=True)
        MyMIDI.addUniversalSysEx(track, time, code, subcode, payload, realTime=True)
        MyMIDI.close()
        self.assertEqual(2, len(MyMIDI.tracks[1].eventList))


def suite():
    MIDISuite = unittest.TestLoader().loadTestsFromTestCase(TestMIDIUtils)

    return MIDISuite


if __name__ == '__main__':
    print("Begining MIDIUtil Test Suite")
    MIDISuite = suite()
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    return_value = not runner.run(MIDISuite).wasSuccessful()
    sys.exit(return_value)


