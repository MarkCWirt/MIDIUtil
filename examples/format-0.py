from midiutil import MIDIFile

song = MIDIFile(file_format=0)
track = 0
song.addTempo(track, 0, 120)
song.addNote(track, channel=0, pitch=60, time=0, duration=1, volume=90)
song.addNote(track, channel=1, pitch=64, time=1, duration=1, volume=80)

with open("format-0.mid", "wb") as output:
    song.writeFile(output)
