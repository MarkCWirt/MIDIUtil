#-----------------------------------------------------------------------------
# Name:        miditest.py
# Purpose:     Unit testing harness for midiutil
#
# Author:      Mark Conway Wirt <emergentmusics) at (gmail . com>
#
# Created:     2008/04/17
# Copyright:   (c) 2009-2016, Mark Conway Wirt
# License:     Please see License.txt for the terms under which this
#              software is distributed.
#-----------------------------------------------------------------------------


from __future__ import division, print_function
import sys,  struct

import unittest
from midiutil.MidiFile import MIDIFile, writeVarLength,  \
    frequencyTransform,  returnFrequency, TICKSPERBEAT

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

class TestMIDIUtils(unittest.TestCase):
    
    def testWriteVarLength(self):
        self.assertEqual(writeVarLength(0x70), [0x70])
        self.assertEqual(writeVarLength(0x80), [0x81, 0x00])
        self.assertEqual(writeVarLength(0x1FFFFF), [0xFF, 0xFF, 0x7F])
        self.assertEqual(writeVarLength(0x08000000), [0xC0, 0x80, 0x80, 0x00])
        
    def testAddNote(self):
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(0, 0, 100,0,1,100)
        self.assertEqual(MyMIDI.tracks[0].eventList[0].type, "note")
        self.assertEqual(MyMIDI.tracks[0].eventList[0].pitch, 100)
        self.assertEqual(MyMIDI.tracks[0].eventList[0].time, 0)
        self.assertEqual(MyMIDI.tracks[0].eventList[0].duration, 1)
        self.assertEqual(MyMIDI.tracks[0].eventList[0].volume, 100)
        
    def testShiftTrack(self):
        time = 1
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(0, 0, 100,time,1,100)
        self.assertEqual(MyMIDI.tracks[0].eventList[0].type, "note")
        self.assertEqual(MyMIDI.tracks[0].eventList[0].pitch, 100)
        self.assertEqual(MyMIDI.tracks[0].eventList[0].time, time)
        self.assertEqual(MyMIDI.tracks[0].eventList[0].duration, 1)
        self.assertEqual(MyMIDI.tracks[0].eventList[0].volume, 100)
        MyMIDI.shiftTracks()
        self.assertEqual(MyMIDI.tracks[0].eventList[0].time, 0)

    def testDeinterleaveNotes(self):
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(0, 0, 100, 0, 2, 100)
        MyMIDI.addNote(0, 0, 100, 1, 2, 100)
        MyMIDI.close()
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].time,  0)
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[1].type, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[1].time,  TICKSPERBEAT)
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[2].type, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[2].time,  0)
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[3].type, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[3].time,  TICKSPERBEAT * 2)
        
    def testTimeShift(self):
        
        # With one track
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(0, 0, 100, 5, 1, 100)
        MyMIDI.close()
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].time,  0)
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[1].type, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[1].time,  TICKSPERBEAT)
        
        # With two tracks
        MyMIDI = MIDIFile(2)
        MyMIDI.addNote(0, 0, 100, 5, 1, 100)
        MyMIDI.addNote(1, 0, 100, 6, 1, 100)
        MyMIDI.close()
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].time,  0)
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[1].type, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[1].time,  TICKSPERBEAT)
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].type, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].time,  TICKSPERBEAT)
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].type, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].time,  TICKSPERBEAT)
        
        # Negative Time
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(0, 0, 100, -5, 1, 100)
        MyMIDI.close()
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].time,  0)
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[1].type, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[1].time,  TICKSPERBEAT)
        
        # Negative time, two tracks
        
        MyMIDI = MIDIFile(2)
        MyMIDI.addNote(0, 0, 100, -1, 1, 100)
        MyMIDI.addNote(1, 0, 100, 0, 1, 100)
        MyMIDI.close()
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].time,  0)
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[1].type, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[1].time,  TICKSPERBEAT)
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].type, 'NoteOn')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[0].time,  TICKSPERBEAT)
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].type, 'NoteOff')
        self.assertEqual(MyMIDI.tracks[1].MIDIEventList[1].time,  TICKSPERBEAT)
 
    def testFrequency(self):
        freq = frequencyTransform(8.1758)
        self.assertEqual(freq[0],  0x00)
        self.assertEqual(freq[1],  0x00)
        self.assertEqual(freq[2],  0x00)
        freq = frequencyTransform(8.66196) # 8.6620 in MIDI documentation
        self.assertEqual(freq[0],  0x01)
        self.assertEqual(freq[1],  0x00)
        self.assertEqual(freq[2],  0x00)
        freq = frequencyTransform(440.00)
        self.assertEqual(freq[0],  0x45)
        self.assertEqual(freq[1],  0x00)
        self.assertEqual(freq[2],  0x00)
        freq = frequencyTransform(440.0016)
        self.assertEqual(freq[0],  0x45)
        self.assertEqual(freq[1],  0x00)
        self.assertEqual(freq[2],  0x01)
        freq = frequencyTransform(439.9984)
        self.assertEqual(freq[0],  0x44)
        self.assertEqual(freq[1],  0x7f)
        self.assertEqual(freq[2],  0x7f)
        freq = frequencyTransform(8372.0190)
        self.assertEqual(freq[0],  0x78)
        self.assertEqual(freq[1],  0x00)
        self.assertEqual(freq[2],  0x00)
        freq = frequencyTransform(8372.062) #8372.0630 in MIDI documentation
        self.assertEqual(freq[0],  0x78)
        self.assertEqual(freq[1],  0x00)
        self.assertEqual(freq[2],  0x01)
        freq = frequencyTransform(13289.7300)
        self.assertEqual(freq[0],  0x7F)
        self.assertEqual(freq[1],  0x7F)
        self.assertEqual(freq[2],  0x7E)
        freq = frequencyTransform(12543.8760)
        self.assertEqual(freq[0],  0x7F)
        self.assertEqual(freq[1],  0x00)
        self.assertEqual(freq[2],  0x00)
        freq = frequencyTransform(8.2104) # Just plain wrong in documentation, as far as I can tell.
        #self.assertEqual(freq[0],  0x0)
        #self.assertEqual(freq[1],  0x0)
        #self.assertEqual(freq[2],  0x1)
        
        # Test the inverse
        testFreq = 15.0
        accuracy = 0.00001
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy*testFreq), True)
        testFreq = 200.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy*testFreq), True)
        testFreq = 400.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy*testFreq), True)
        testFreq = 440.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy*testFreq), True)
        testFreq = 1200.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy*testFreq), True)
        testFreq = 5000.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy*testFreq), True)
        testFreq = 12000.0
        x = returnFrequency(frequencyTransform(testFreq))
        delta = abs(testFreq - x)
        self.assertEqual(delta < (accuracy*testFreq), True)
        
    
    def testSysEx(self):
        #import pdb; pdb.set_trace()
        MyMIDI = MIDIFile(1)
        MyMIDI.addSysEx(0,0, 0, struct.pack('>B', 0x01))
        MyMIDI.close()
        data = Decoder(MyMIDI.tracks[0].MIDIdata)
        
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'SysEx')
        
        self.assertEqual(struct.unpack('>B', data[0])[0], 0x00)
        self.assertEqual(struct.unpack('>B', data[1])[0], 0xf0)
        self.assertEqual(struct.unpack('>B', data[2])[0], 3)
        self.assertEqual(struct.unpack('>B', data[3])[0], 0x00)
        self.assertEqual(struct.unpack('>B', data[4])[0], 0x01)
        self.assertEqual(struct.unpack('>B', data[5])[0], 0xf7)
        
    def testTempo(self):
        #import pdb; pdb.set_trace()
        tempo = 60
        MyMIDI = MIDIFile(1)
        MyMIDI.addTempo(0, 0, tempo)
        MyMIDI.close()
        
        data = Decoder(MyMIDI.tracks[0].MIDIdata)
        
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'Tempo')
        
        self.assertEqual(struct.unpack('>B', data[0])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[1])[0], 0xff) # Code
        self.assertEqual(struct.unpack('>B', data[2])[0], 0x51)
        self.assertEqual(struct.unpack('>B', data[3])[0], 0x03)
        self.assertEqual(data[4:7], struct.pack('>L', int(60000000/tempo))[1:4])
        
    def testProgramChange(self):
        #import pdb; pdb.set_trace()
        program = 10
        channel = 0
        MyMIDI = MIDIFile(1)
        MyMIDI.addProgramChange(0, channel, 0, program)
        MyMIDI.close()
        
        data = Decoder(MyMIDI.tracks[0].MIDIdata)
        
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'ProgramChange')
        self.assertEqual(struct.unpack('>B', data[0])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[1])[0], 0xC << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[2])[0], program)
        
    def testTrackName(self):
        #import pdb; pdb.set_trace()
        track_name = "track"
        MyMIDI = MIDIFile(1)
        MyMIDI.addTrackName(0, 0, track_name)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[0].MIDIdata)

        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'TrackName')
        self.assertEqual(struct.unpack('>B', data[0])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[1])[0], 0xFF) # Code
        self.assertEqual(struct.unpack('>B', data[2])[0], 0x03) # subcodes
        
    def testTuningBank(self):
        #import pdb; pdb.set_trace()
        bank = 1
        channel = 0
        MyMIDI = MIDIFile(1)
        MyMIDI.changeTuningBank(0, 0, 0, bank)
        MyMIDI.close()
        
        data = Decoder(MyMIDI.tracks[0].MIDIdata)
        
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'ControllerEvent')
        
        self.assertEqual(struct.unpack('>B', data[0])[0],  0x00) # time
        self.assertEqual(struct.unpack('>B', data[1])[0],  0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[2])[0],  0x65) # Controller Number
        self.assertEqual(struct.unpack('>B', data[3])[0],  0x0) # Controller Value
        self.assertEqual(struct.unpack('>B', data[4])[0],  0x00) # time
        self.assertEqual(struct.unpack('>B', data[5])[0],  0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[6])[0],  0x64) # Controller Number
        self.assertEqual(struct.unpack('>B', data[7])[0],  0x4) # Controller Value
        self.assertEqual(struct.unpack('>B', data[8])[0],  0x00) # time
        self.assertEqual(struct.unpack('>B', data[9])[0],  0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[10])[0], 0x06) # Bank MSB
        self.assertEqual(struct.unpack('>B', data[11])[0], 0x00) # Value
        self.assertEqual(struct.unpack('>B', data[12])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[13])[0], 0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[14])[0], 0x26) # Bank LSB
        self.assertEqual(struct.unpack('>B', data[15])[0], 0x01) # Bank value (bank number)
        
    def testTuningProgram(self):
        #import pdb; pdb.set_trace()
        program = 1
        channel = 0
        MyMIDI = MIDIFile(1)
        MyMIDI.changeTuningProgram(0, 0, 0, program)
        MyMIDI.close()

        data = Decoder(MyMIDI.tracks[0].MIDIdata)
        
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'ControllerEvent')
        
        self.assertEqual(struct.unpack('>B', data[0])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[1])[0], 0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[2])[0], 0x65) # Controller Number
        self.assertEqual(struct.unpack('>B', data[3])[0], 0x0) # Controller Value
        self.assertEqual(struct.unpack('>B', data[4])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[5])[0], 0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[6])[0], 0x64) # Controller Number
        self.assertEqual(struct.unpack('>B', data[7])[0], 0x03) # Controller Value
        self.assertEqual(struct.unpack('>B', data[8])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[9])[0], 0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[10])[0], 0x06) # Bank MSB
        self.assertEqual(struct.unpack('>B', data[11])[0], 0x00) # Value
        self.assertEqual(struct.unpack('>B', data[12])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[13])[0], 0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[14])[0], 0x26) # Bank LSB
        self.assertEqual(struct.unpack('>B', data[15])[0], 0x01) # Bank value (bank number)
        
    def testNRPNCall(self):
        #import pdb; pdb.set_trace()
        track = 0
        time = 0
        channel = 0
        controller_msb = 1
        controller_lsb =  2
        data_msb = 3
        data_lsb = 4
        MyMIDI = MIDIFile(1)
        MyMIDI.makeNRPNCall(track, channel, time, controller_msb, controller_lsb, data_msb, data_lsb)
        MyMIDI.close()
        
        data = Decoder(MyMIDI.tracks[0].MIDIdata)
        
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'ControllerEvent')
        
        self.assertEqual(struct.unpack('>B', data[0])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[1])[0], 0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[2])[0], 99) # Controller Number
        self.assertEqual(struct.unpack('>B', data[3])[0], controller_msb) # Controller Value
        self.assertEqual(struct.unpack('>B', data[4])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[5])[0], 0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[6])[0], 98) # Controller Number
        self.assertEqual(struct.unpack('>B', data[7])[0], controller_lsb) # Controller Value
        self.assertEqual(struct.unpack('>B', data[8])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[9])[0], 0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[10])[0], 0x06) # Bank MSB
        self.assertEqual(struct.unpack('>B', data[11])[0], data_msb) # Value
        self.assertEqual(struct.unpack('>B', data[12])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[13])[0], 0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[14])[0], 0x26) # Bank LSB
        self.assertEqual(struct.unpack('>B', data[15])[0], data_lsb) # Bank value (bank number)
        
    def testAddControllerEvent(self):
        #import pdb; pdb.set_trace()
        track = 0
        time = 0
        channel = 3
        controller_number = 1
        parameter =  2
        MyMIDI = MIDIFile(1)
        MyMIDI.addControllerEvent(track, channel, time, controller_number, parameter)
        MyMIDI.close()
        
        data = Decoder(MyMIDI.tracks[0].MIDIdata)
        
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'ControllerEvent')

        self.assertEqual(struct.unpack('>B', data[0])[0], 0x00) # time
        self.assertEqual(struct.unpack('>B', data[1])[0], 0xB << 4 | channel) # Code
        self.assertEqual(struct.unpack('>B', data[2])[0], controller_number) # Controller Number
        self.assertEqual(struct.unpack('>B', data[3])[0], parameter) # Controller Value
        
    def testNonRealTimeUniversalSysEx(self):
        MyMIDI = MIDIFile(1)
        MyMIDI.addUniversalSysEx(0,0, 1, 2, struct.pack('>B', 0x01), realTime=False)
        MyMIDI.close()
        
        data = Decoder(MyMIDI.tracks[0].MIDIdata)
        
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'UniversalSysEx')
        
        self.assertEqual(struct.unpack('>B', data[0])[0], 0x00)
        self.assertEqual(struct.unpack('>B', data[1])[0], 0xf0)
        self.assertEqual(struct.unpack('>B', data[2])[0], 6)
        self.assertEqual(struct.unpack('>B', data[3])[0], 0x7E)
        self.assertEqual(struct.unpack('>B', data[4])[0], 0x7F)
        self.assertEqual(struct.unpack('>B', data[5])[0], 0x01)
        self.assertEqual(struct.unpack('>B', data[6])[0], 0x02)
        self.assertEqual(struct.unpack('>B', data[7])[0], 0x01)
        self.assertEqual(struct.unpack('>B', data[8])[0], 0xf7)
        
    def testRealTimeUniversalSysEx(self):
        MyMIDI = MIDIFile(1)
        MyMIDI.addUniversalSysEx(0,0, 1, 2, struct.pack('>B', 0x01), realTime=True)
        MyMIDI.close()
        
        data = Decoder(MyMIDI.tracks[0].MIDIdata)
        
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'UniversalSysEx')
        
        self.assertEqual(struct.unpack('>B', data[0])[0], 0x00)
        self.assertEqual(struct.unpack('>B', data[1])[0], 0xf0)
        self.assertEqual(struct.unpack('>B', data[2])[0], 6)
        self.assertEqual(struct.unpack('>B', data[3])[0], 0x7F)
        self.assertEqual(struct.unpack('>B', data[4])[0], 0x7F)
        self.assertEqual(struct.unpack('>B', data[5])[0], 0x01)
        self.assertEqual(struct.unpack('>B', data[6])[0], 0x02)
        self.assertEqual(struct.unpack('>B', data[7])[0], 0x01)
        self.assertEqual(struct.unpack('>B', data[8])[0], 0xf7)
        
    def testTuning(self):
        MyMIDI = MIDIFile(1)
        MyMIDI.changeNoteTuning(0, [(1, 440), (2, 880)])
        MyMIDI.close()
        
        data = Decoder(MyMIDI.tracks[0].MIDIdata)
        
        self.assertEqual(MyMIDI.tracks[0].MIDIEventList[0].type, 'UniversalSysEx')
        
        self.assertEqual(struct.unpack('>B', data[0])[0], 0x00)
        self.assertEqual(struct.unpack('>B', data[1])[0], 0xf0)
        self.assertEqual(struct.unpack('>B', data[2])[0], 15)
        self.assertEqual(struct.unpack('>B', data[3])[0], 0x7E)
        self.assertEqual(struct.unpack('>B', data[4])[0], 0x7F)
        self.assertEqual(struct.unpack('>B', data[5])[0], 0x08)
        self.assertEqual(struct.unpack('>B', data[6])[0], 0x02)
        self.assertEqual(struct.unpack('>B', data[7])[0], 0x00)
        self.assertEqual(struct.unpack('>B', data[8])[0], 0x2)
        self.assertEqual(struct.unpack('>B', data[9])[0], 0x1)
        self.assertEqual(struct.unpack('>B', data[10])[0], 69)
        self.assertEqual(struct.unpack('>B', data[11])[0], 0)
        self.assertEqual(struct.unpack('>B', data[12])[0], 0)
        self.assertEqual(struct.unpack('>B', data[13])[0], 0x2)
        self.assertEqual(struct.unpack('>B', data[14])[0], 81)
        self.assertEqual(struct.unpack('>B', data[15])[0], 0)
        self.assertEqual(struct.unpack('>B', data[16])[0], 0)
        self.assertEqual(struct.unpack('>B', data[17])[0], 0xf7)
        
    def testWriteFile(self):
        # Just to make sure the stream can be written without throwing an error.
        MyMIDI = MIDIFile(1)
        MyMIDI.addNote(0, 0, 100,0,1,100)
        with open("/tmp/test.mid", "wb") as output_file:
            MyMIDI.writeFile(output_file)

def suite():
    MIDISuite = unittest.TestLoader().loadTestsFromTestCase(TestMIDIUtils)

    return MIDISuite

if __name__ == '__main__':
    print("Begining MIDIUtil Test Suite")
    MIDISuite = suite()
    unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(MIDISuite)


