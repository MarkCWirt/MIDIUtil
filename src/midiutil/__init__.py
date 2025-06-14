from midiutil.MidiFile import *
track = 0
channel = 0
volume = 100
tempo = 80
duration = 2
beats_per_measure = 4

chords = [
    ["C4", "Eb4", "G4"],   # Cm
    ["Ab3", "C4", "Eb4"],  # Ab
    ["Eb3", "G3", "Bb3"],  # Eb
    ["G3", "B3", "D4"],    # G
    ["F3", "Ab3", "C4"],   # Fm
    ["Bb2", "D3", "F3"],   # Bb
    ["G3", "B3", "D4"],    # G
    ["C4", "Eb4", "G4"]    # Cm
]

note_map = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

def note_to_midi(note):
    name = note[:-1]
    octave = int(note[-1])
    return 12 * (octave + 1) + note_map[name]

midi = MIDIFile(1)
midi.addTempo(track, 0, tempo)

time = 0
for chord in chords:
    for note in chord:
        midi.addNote(track, channel, note_to_midi(note), time, duration * beats_per_measure, volume)
    time += duration * beats_per_measure

with open("epikus_akkordmenet.mid", "wb") as f:
    midi.writeFile(f)
__all__ = ['MIDIFile', 'MAJOR', 'MINOR', 'SHARPS', 'FLATS']
