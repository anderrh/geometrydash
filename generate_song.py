#!/usr/bin/env python3
"""
Generate a .MOD file with a simple chord progression for Game Boy.
Uses samples from template.mod for authentic Game Boy sound.
"""

import struct

# MOD note period table (Amiga periods)
NOTE_PERIODS = {
    'C-1': 856, 'C#1': 808, 'D-1': 762, 'D#1': 720, 'E-1': 678, 'F-1': 640,
    'F#1': 604, 'G-1': 570, 'G#1': 538, 'A-1': 508, 'A#1': 480, 'B-1': 453,
    'C-2': 428, 'C#2': 404, 'D-2': 381, 'D#2': 360, 'E-2': 339, 'F-2': 320,
    'F#2': 302, 'G-2': 285, 'G#2': 269, 'A-2': 254, 'A#2': 240, 'B-2': 226,
    'C-3': 214, 'C#3': 202, 'D-3': 190, 'D#3': 180, 'E-3': 170, 'F-3': 160,
    'F#3': 151, 'G-3': 143, 'G#3': 135, 'A-3': 127, 'A#3': 120, 'B-3': 113,
    'C-4': 107, 'C#4': 101, 'D-4': 95, 'D#4': 90, 'E-4': 85, 'F-4': 80,
    'F#4': 76, 'G-4': 71, 'G#4': 67, 'A-4': 64, 'A#4': 60, 'B-4': 57,
}

def read_template_mod(path):
    """Read template.mod and extract sample headers and data"""
    with open(path, 'rb') as f:
        data = f.read()

    # Title: 20 bytes
    title = data[0:20]

    # 31 sample headers: 30 bytes each
    sample_headers = []
    sample_lengths = []
    offset = 20
    for i in range(31):
        header = data[offset:offset+30]
        sample_headers.append(header)
        # Length is at bytes 22-23 (big endian, in words)
        length_words = struct.unpack('>H', header[22:24])[0]
        sample_lengths.append(length_words * 2)  # Convert to bytes
        offset += 30

    # Song length and restart
    song_length = data[offset]
    restart = data[offset + 1]
    offset += 2

    # Pattern table: 128 bytes
    pattern_table = data[offset:offset+128]
    offset += 128

    # Identifier (M.K., etc)
    identifier = data[offset:offset+4]
    offset += 4

    # Find number of patterns (highest pattern number + 1)
    num_patterns = max(pattern_table[:song_length]) + 1

    # Skip pattern data to get to samples
    pattern_data_size = num_patterns * 64 * 4 * 4  # 64 rows, 4 channels, 4 bytes
    sample_data_offset = offset + pattern_data_size

    # Extract sample data
    samples_data = []
    current_offset = sample_data_offset
    for length in sample_lengths:
        if length > 0:
            samples_data.append(data[current_offset:current_offset+length])
            current_offset += length
        else:
            samples_data.append(b'')

    return {
        'headers': sample_headers,
        'lengths': sample_lengths,
        'data': samples_data,
        'identifier': identifier,
    }

def encode_note(period, sample, effect=0, effect_param=0):
    """Encode a single note for MOD format (4 bytes)"""
    if period == 0 and sample == 0:
        return bytes([0, 0, effect, effect_param])

    sample_high = (sample >> 4) & 0x0F
    sample_low = (sample & 0x0F) << 4
    period_high = (period >> 8) & 0x0F
    period_low = period & 0xFF

    byte1 = (sample_high << 4) | period_high
    byte2 = period_low
    byte3 = sample_low | ((effect >> 4) & 0x0F)
    byte4 = effect_param

    return bytes([byte1, byte2, byte3, byte4])

def create_pattern(notes_ch1, notes_ch2, notes_ch3, notes_ch4, set_speed=None):
    """Create a 64-row pattern with notes on 4 channels.
    set_speed: if provided, set Fxx speed command on row 0, channel 3
    """
    pattern = bytearray(64 * 4 * 4)

    for i in range(64 * 4):
        pattern[i*4:i*4+4] = bytes([0, 0, 0, 0])

    for channel, notes in enumerate([notes_ch1, notes_ch2, notes_ch3, notes_ch4]):
        for row, note_name, sample, volume in notes:
            if row >= 64:
                continue
            period = NOTE_PERIODS.get(note_name, 0)
            # Cxx = set volume
            effect = 0x0C
            effect_param = volume
            note_data = encode_note(period, sample, effect, effect_param)
            offset = row * 16 + channel * 4
            pattern[offset:offset+4] = note_data

    # Set speed on row 0 if requested (use channel 3 / index 3)
    # Fxx effect: F01-F1F = speed (ticks per row), F20+ = BPM
    if set_speed is not None:
        # Put speed command on row 0, channel 3 (won't overwrite if no note there)
        offset = 0 * 16 + 3 * 4  # row 0, channel 3
        # Read existing data
        existing = pattern[offset:offset+4]
        # If there's no note, just set the effect
        if existing[0] == 0 and existing[1] == 0:
            pattern[offset:offset+4] = encode_note(0, 0, 0x0F, set_speed)
        else:
            # There's a note - modify the effect bytes only
            pattern[offset+2] = (existing[2] & 0xF0) | 0x0F
            pattern[offset+3] = set_speed

    return bytes(pattern)

def create_empty_pattern():
    """Create an empty 64-row pattern"""
    return bytes(64 * 4 * 4)

def main():
    # Read template.mod for samples
    template = read_template_mod('template.mod')

    print("Template samples found:")
    for i, header in enumerate(template['headers']):
        name = header[0:22].decode('ascii', errors='replace').strip('\x00')
        length = template['lengths'][i]
        if length > 0:
            print(f"  {i+1}: {name} ({length} bytes)")

    # Sample assignments based on template.mod:
    # 1: Ch 1&2 - 25% Pulse
    # 2: Ch 1&2 - 50% Pulse
    # 3: Ch 1&2 - 75% Pulse
    # 4: Ch 1&2 - 12.5% Pulse
    # 9: Ch 3 - Random Waveform (wave channel)
    # 14: Ch 3 - Square Wave
    # 15: Ch 3 - Sine Wave

    # Use smoother wave channel instruments (64 bytes, less clicky)
    BASS_SAMPLE = 13     # Sawtooth Wave - smooth and full

    # Alternating note pairs - each pair repeats 4 times (8 notes per pattern)
    # Format: (note1, note2) - these alternate, with note2 being ~5th above note1
    # "4 apart" = perfect 5th (7 semitones)

    two_note_pairs = [
        # Section A: Original request - C G C G C G C G, then G D, then A E, then F C
        ('C-2', 'G-2'),   # C and G (perfect 5th)
        ('G-2', 'D-3'),   # G and D (perfect 5th)
        ('A-2', 'E-3'),   # A and E (perfect 5th)
        ('F-2', 'C-3'),   # F and C (perfect 5th)

        # Section B: More pairs - building familiarity
        ('D-2', 'A-2'),   # D and A
        ('E-2', 'B-2'),   # E and B
        ('G-2', 'D-3'),   # G and D again
        ('C-2', 'G-2'),   # back to C and G

        # Section C: Rhymes with A but higher register - leaning in
        ('C-3', 'G-3'),   # C and G higher (echo of section A)
        ('G-3', 'D-4'),   # G and D higher
        ('A-2', 'E-3'),   # A and E (familiar)
        ('F-3', 'C-4'),   # F and C higher

        # Section D: Going off the rails - unexpected intervals
        ('C-2', 'F#2'),   # Tritone! (the devil's interval)
        ('G-2', 'C#3'),   # Another tritone
        ('D-2', 'G#2'),   # Tritone again
        ('A-2', 'D#3'),   # Tritone - tension!

        # Section E: Chromatic descent - sliding down
        ('C-3', 'B-2'),   # Half step down
        ('B-2', 'A#2'),   # Keep sliding
        ('A#2', 'A-2'),   # More sliding
        ('A-2', 'G#2'),   # Chromatic tension

        # Section F: Resolution - back to familiar but with twist
        ('G-2', 'D-3'),   # Familiar G-D
        ('C-2', 'G-2'),   # Back home to C-G
        ('F-2', 'C-3'),   # F-C comfort
        ('C-2', 'E-2'),   # End on major 3rd - warm resolution

        # Section G: Wild octave jumps
        ('C-2', 'C-3'),   # Octave jump
        ('G-2', 'G-3'),   # Octave jump
        ('D-2', 'D-3'),   # Octave jump
        ('A-2', 'A-3'),   # Octave jump

        # Section H: Final return home
        ('C-2', 'G-2'),   # Classic C-G
        ('G-2', 'D-3'),   # G-D
        ('C-2', 'G-2'),   # C-G again
        ('C-2', 'G-2'),   # Hold on home
    ]

    # Four note pairs - just root and fifth alternating
    four_note_sequences = [
        # Familiar progressions
        ('C-2', 'G-2'),   # C major feel
        ('G-2', 'D-3'),   # G major feel
        ('A-2', 'E-3'),   # A minor feel
        ('F-2', 'C-3'),   # F major feel
        # Wilder ones
        ('E-2', 'C-3'),   # Minor 6th - darker
        ('D-2', 'B-2'),   # Major 6th
        ('C-2', 'A-2'),   # Minor 6th down
        ('G-2', 'E-3'),   # Major 6th up
    ]

    patterns = []

    # Generate two-note alternating patterns
    # Each pattern = 64 rows, 8 notes per pattern (8 rows each)
    for pair in two_note_pairs:
        ch1_notes = []
        ch2_notes = []  # quiet accompaniment
        ch3_notes = []
        ch4_notes = []

        note1, note2 = pair
        rows_per_note = 8  # 8 rows per note, 8 notes = 64 rows

        for i in range(8):  # 8 notes: n1 n2 n1 n2 n1 n2 n1 n2
            row = i * rows_per_note
            note = note1 if i % 2 == 0 else note2

            # Main bass note on channel 1 only - clean, no accompaniment
            ch1_notes.append((row, note, BASS_SAMPLE, 64))

        speed = 2 if len(patterns) == 0 else None  # Faster tempo
        pattern = create_pattern(ch1_notes, ch2_notes, ch3_notes, ch4_notes, set_speed=speed)
        patterns.append(pattern)

    # Generate additional patterns with the four_note_sequences
    for seq in four_note_sequences:
        ch1_notes = []
        ch2_notes = []
        ch3_notes = []
        ch4_notes = []

        note1, note2 = seq
        rows_per_note = 8

        for i in range(8):
            row = i * rows_per_note
            note = note1 if i % 2 == 0 else note2
            ch1_notes.append((row, note, BASS_SAMPLE, 64))

        pattern = create_pattern(ch1_notes, ch2_notes, ch3_notes, ch4_notes)
        patterns.append(pattern)

    # Create pattern order - at speed 2, each pattern is ~1.02 seconds
    # Max 128 entries = ~130 seconds = ~2.2 minutes at speed 2
    pattern_order = []

    # Play through all patterns, then add extra from the beginning
    pattern_order.extend(range(len(patterns)))
    pattern_order.extend(range(len(patterns)))
    pattern_order.extend(range(len(patterns)))
    pattern_order.extend(range(len(patterns)))  # Fill to max

    # MOD format supports up to 128 entries in pattern order
    if len(pattern_order) > 128:
        pattern_order = pattern_order[:128]

    # At speed 2 (ticks per row), 125 BPM: each row = 0.016 sec, 64 rows = 1.02 sec per pattern
    print(f"\nGenerated {len(patterns)} patterns, song order has {len(pattern_order)} entries")
    print(f"Estimated duration: {len(pattern_order) * 1.02:.1f} seconds ({len(pattern_order) * 1.02 / 60:.1f} minutes)")

    # Write the MOD file
    output_path = '/home/danielrh/dev/geometrydash/gamesong.mod'
    with open(output_path, 'wb') as f:
        # Title (20 bytes)
        title = b'GB Chord Song'.ljust(20, b'\x00')
        f.write(title)

        # Sample headers (31 x 30 bytes) - copy from template
        for header in template['headers']:
            f.write(header)

        # Song length
        f.write(bytes([len(pattern_order)]))

        # Restart position
        f.write(bytes([0]))

        # Pattern table (128 bytes)
        pattern_table = bytes(pattern_order + [0] * (128 - len(pattern_order)))
        f.write(pattern_table)

        # Identifier
        f.write(template['identifier'])

        # Pattern data
        for pattern in patterns:
            f.write(pattern)

        # Sample data - copy from template
        for sample_data in template['data']:
            f.write(sample_data)

    import os
    file_size = os.path.getsize(output_path)
    template_size = os.path.getsize('/home/danielrh/dev/geometrydash/template.mod')
    print(f"\nOutput: {output_path}")
    print(f"Size: {file_size} bytes (template was {template_size} bytes)")

if __name__ == '__main__':
    main()
