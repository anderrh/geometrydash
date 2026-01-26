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

    # Wave channel sample (64 bytes) - loops cleaner than short pulse waves
    BASS_SAMPLE = 12     # Pulse+Tri Wave - softer, 64 bytes

    # Alternating note pairs - each pair repeats 4 times (8 notes per pattern)
    # Format: (note1, note2) - these alternate, with note2 being ~5th above note1
    # "4 apart" = perfect 5th (7 semitones)

    # ============================================
    # PART 1: Opening - the good beginning (patterns 0-7)
    # ============================================
    opening_pairs = [
        ('C-2', 'G-2'),   # C and G (perfect 5th)
        ('G-2', 'D-3'),   # G and D (perfect 5th)
        ('A-2', 'E-3'),   # A and E (perfect 5th)
        ('F-2', 'C-3'),   # F and C (perfect 5th)
        ('D-2', 'A-2'),   # D and A
        ('E-2', 'B-2'),   # E and B
        ('G-2', 'D-3'),   # G and D again
        ('C-2', 'G-2'),   # back to C and G
    ]

    # ============================================
    # PART 2: Melodic hooks in MINOR KEY with variations
    # C minor scale: C D Eb F G Ab Bb C
    # Each variation shifts or surprises
    # ============================================

    # B1: Original C minor melodic hook (patterns 8-15)
    melodic_B1 = [
        ['C-2', 'D-2', 'D#2', 'G-2', 'D#2', 'D-2', 'C-2', 'G-2'],      # Rising minor
        ['G-2', 'G#2', 'A#2', 'D-3', 'A#2', 'G#2', 'G-2', 'D-3'],      # Answer in minor
        ['C-2', 'D#2', 'G-2', 'C-3', 'G-2', 'D#2', 'C-2', 'G-2'],      # Minor arpeggio
        ['G#2', 'G-2', 'D#2', 'D-2', 'C-2', 'D-2', 'D#2', 'C-2'],      # Descending resolve
        ['C-3', 'D-3', 'D#3', 'G-3', 'D#3', 'D-3', 'C-3', 'G-2'],      # Higher register
        ['G-3', 'D#3', 'D-3', 'C-3', 'A#2', 'G#2', 'G-2', 'C-3'],      # Descending minor
        ['C-2', 'G-2', 'D#2', 'G-2', 'C-3', 'G-2', 'D#2', 'C-2'],      # Bouncy minor
        ['G-2', 'C-3', 'D#3', 'D-3', 'C-3', 'G-2', 'D#2', 'C-2'],      # Final phrase
    ]

    # B2: Shifted UP 2 semitones (D minor) - surprise! (patterns 16-23)
    melodic_B2 = [
        ['D-2', 'E-2', 'F-2', 'A-2', 'F-2', 'E-2', 'D-2', 'A-2'],      # D minor rising
        ['A-2', 'A#2', 'C-3', 'E-3', 'C-3', 'A#2', 'A-2', 'E-3'],      # Answer
        ['D-2', 'F-2', 'A-2', 'D-3', 'A-2', 'F-2', 'D-2', 'A-2'],      # Arpeggio
        ['A#2', 'A-2', 'F-2', 'E-2', 'D-2', 'E-2', 'F-2', 'D-2'],      # Resolve
        ['D-3', 'E-3', 'F-3', 'A-3', 'F-3', 'E-3', 'D-3', 'A-2'],      # High
        ['A-3', 'F-3', 'E-3', 'D-3', 'C-3', 'A#2', 'A-2', 'D-3'],      # Descend
        ['D-2', 'A-2', 'F-2', 'A-2', 'D-3', 'A-2', 'F-2', 'D-2'],      # Bouncy
        ['A-2', 'D-3', 'F-3', 'E-3', 'D-3', 'A-2', 'F-2', 'D-2'],      # Final
    ]

    # B3: Shifted UP another 2 (E minor) - building tension! (patterns 24-31)
    melodic_B3 = [
        ['E-2', 'F#2', 'G-2', 'B-2', 'G-2', 'F#2', 'E-2', 'B-2'],      # E minor rising
        ['B-2', 'C-3', 'D-3', 'F#3', 'D-3', 'C-3', 'B-2', 'F#3'],      # Answer
        ['E-2', 'G-2', 'B-2', 'E-3', 'B-2', 'G-2', 'E-2', 'B-2'],      # Arpeggio
        ['C-3', 'B-2', 'G-2', 'F#2', 'E-2', 'F#2', 'G-2', 'E-2'],      # Resolve
        ['E-3', 'F#3', 'G-3', 'B-3', 'G-3', 'F#3', 'E-3', 'B-2'],      # High
        ['B-3', 'G-3', 'F#3', 'E-3', 'D-3', 'C-3', 'B-2', 'E-3'],      # Descend
        ['E-2', 'B-2', 'G-2', 'B-2', 'E-3', 'B-2', 'G-2', 'E-2'],      # Bouncy
        ['B-2', 'E-3', 'G-3', 'F#3', 'E-3', 'B-2', 'G-2', 'E-2'],      # Final
    ]

    # B4: SURPRISE - drop to A minor (darker) (patterns 32-39)
    melodic_B4 = [
        ['A-2', 'B-2', 'C-3', 'E-3', 'C-3', 'B-2', 'A-2', 'E-3'],      # A minor - darker!
        ['E-3', 'F-3', 'G-3', 'B-3', 'G-3', 'F-3', 'E-3', 'B-3'],      # Answer high
        ['A-2', 'C-3', 'E-3', 'A-3', 'E-3', 'C-3', 'A-2', 'E-3'],      # Arpeggio
        ['F-3', 'E-3', 'C-3', 'B-2', 'A-2', 'B-2', 'C-3', 'A-2'],      # Resolve
        ['A-3', 'B-3', 'C-4', 'E-4', 'C-4', 'B-3', 'A-3', 'E-3'],      # Very high!
        ['E-4', 'C-4', 'B-3', 'A-3', 'G-3', 'F-3', 'E-3', 'A-3'],      # Big descend
        ['A-2', 'E-3', 'C-3', 'E-3', 'A-3', 'E-3', 'C-3', 'A-2'],      # Bouncy
        ['E-3', 'A-3', 'C-4', 'B-3', 'A-3', 'E-3', 'C-3', 'A-2'],      # Final dramatic
    ]

    # ============================================
    # PART 3: Return to opening (reuse patterns 0-7)
    # This is handled in pattern_order below
    # ============================================

    patterns = []

    # Generate opening patterns (alternating two notes) - simple, clean
    for pair in opening_pairs:
        ch1_notes = []
        ch2_notes = []
        ch3_notes = []
        ch4_notes = []

        note1, note2 = pair
        rows_per_note = 8

        for i in range(8):
            row = i * rows_per_note
            note = note1 if i % 2 == 0 else note2
            # Single note, low volume for background music
            ch1_notes.append((row, note, BASS_SAMPLE, 20))

        speed = 2 if len(patterns) == 0 else None
        pattern = create_pattern(ch1_notes, ch2_notes, ch3_notes, ch4_notes, set_speed=speed)
        patterns.append(pattern)

    # Generate all melodic variations - simple, clean
    all_melodic = [melodic_B1, melodic_B2, melodic_B3, melodic_B4]

    for melodic_section in all_melodic:
        for melody in melodic_section:
            ch1_notes = []
            ch2_notes = []
            ch3_notes = []
            ch4_notes = []

            rows_per_note = 8

            for i, note in enumerate(melody):
                row = i * rows_per_note
                if note in NOTE_PERIODS:
                    # Single note, low volume for background music
                    ch1_notes.append((row, note, BASS_SAMPLE, 20))

            pattern = create_pattern(ch1_notes, ch2_notes, ch3_notes, ch4_notes)
            patterns.append(pattern)

    # Create pattern order with clear structure:
    # A: Opening (patterns 0-7) - the good beginning
    # B1: C minor melodic hook (patterns 8-15)
    # B2: D minor - shifted up 2 (patterns 16-23)
    # B3: E minor - shifted up again (patterns 24-31)
    # B4: A minor - surprise drop (patterns 32-39)
    #
    # Structure: A -> B1 -> A -> B2 -> A -> B3 -> A -> B4 -> A -> B1 (back to original)

    pattern_order = []

    # Round 1: Opening + C minor
    pattern_order.extend(range(0, 8))       # A: opening
    pattern_order.extend(range(8, 16))      # B1: C minor

    # Round 2: Opening + D minor (shifted up 2!)
    pattern_order.extend(range(0, 8))       # A: opening (same)
    pattern_order.extend(range(16, 24))     # B2: D minor - surprise shift!

    # Round 3: Opening + E minor (shifted up again!)
    pattern_order.extend(range(0, 8))       # A: opening (same)
    pattern_order.extend(range(24, 32))     # B3: E minor - more tension!

    # Round 4: Opening + A minor (surprise drop!)
    pattern_order.extend(range(0, 8))       # A: opening (same)
    pattern_order.extend(range(32, 40))     # B4: A minor - dramatic!

    # Round 5: Back to original C minor (resolution)
    pattern_order.extend(range(0, 8))       # A: opening (same)
    pattern_order.extend(range(8, 16))      # B1: C minor - back home

    # Round 6: One more D minor then back
    pattern_order.extend(range(0, 8))       # A: opening
    pattern_order.extend(range(16, 24))     # B2: D minor

    # Round 7: Final return to C minor
    pattern_order.extend(range(0, 8))       # A: opening
    pattern_order.extend(range(8, 16))      # B1: C minor - home

    # Round 8: End on opening only (wind down)
    pattern_order.extend(range(0, 8))       # A: opening - final

    # Total: 8 rounds × 16 = 128 entries
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
