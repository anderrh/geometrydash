#!/usr/bin/env python3
"""
Convert Emulicious I/O watchpoint dumps of Game Boy sound registers
into hUGE Tracker V6 .uge files.

Parses register writes to $FF10-$FF3F, reconstructs note events per frame,
and outputs a playable .uge file.
"""

import struct
import re
import sys
import math
from collections import defaultdict

# ============================================
# .uge format constants and helpers
# (borrowed from generate_song.py)
# ============================================

NO_NOTE = 90
UGE_FORMAT_VERSION = 6

def write_uge_shortstring(f, s):
    encoded = s.encode('ascii')[:255]
    f.write(bytes([len(encoded)]))
    f.write(encoded)
    f.write(bytes(255 - len(encoded)))

def write_uge_int(f, value):
    f.write(struct.pack('<i', value))

def write_uge_cell(f, note=NO_NOTE, instrument=0, volume=0, effect_code=0, effect_params=0):
    write_uge_int(f, note)
    write_uge_int(f, instrument)
    write_uge_int(f, volume)
    write_uge_int(f, effect_code)
    f.write(bytes([effect_params & 0xFF]))

def write_uge_instrument(f, type_=0, name="", length=0, length_enabled=False,
                         initial_volume=0, vol_sweep_dir=0, vol_sweep_amount=0,
                         sweep_time=0, sweep_inc_dec=0, sweep_shift=0,
                         duty=2, output_level=0, waveform=0, counter_step=0,
                         subpattern_enabled=False):
    write_uge_int(f, type_)
    write_uge_shortstring(f, name)
    write_uge_int(f, length)
    f.write(bytes([1 if length_enabled else 0]))
    f.write(bytes([initial_volume & 0x0F]))
    write_uge_int(f, vol_sweep_dir)
    f.write(bytes([vol_sweep_amount & 0x07]))
    write_uge_int(f, sweep_time)
    write_uge_int(f, sweep_inc_dec)
    write_uge_int(f, sweep_shift)
    f.write(bytes([duty & 0x03]))
    write_uge_int(f, output_level)
    write_uge_int(f, waveform)
    write_uge_int(f, counter_step)
    f.write(bytes([1 if subpattern_enabled else 0]))
    # Subpattern: 64 empty cells
    for _ in range(64):
        write_uge_cell(f)


# ============================================
# Game Boy sound register definitions
# ============================================

# Register offsets from $FF00
# Channel 1 (Pulse + Sweep)
NR10 = 0x10  # Sweep
NR11 = 0x11  # Length/Duty
NR12 = 0x12  # Volume envelope
NR13 = 0x13  # Freq low
NR14 = 0x14  # Freq high + trigger

# Channel 2 (Pulse)
NR21 = 0x16  # Length/Duty
NR22 = 0x17  # Volume envelope
NR23 = 0x18  # Freq low
NR24 = 0x19  # Freq high + trigger

# Channel 3 (Wave)
NR30 = 0x1A  # Enable
NR31 = 0x1B  # Length
NR32 = 0x1C  # Output level
NR33 = 0x1D  # Freq low
NR34 = 0x1E  # Freq high + trigger

# Channel 4 (Noise)
NR41 = 0x20  # Length
NR42 = 0x21  # Volume envelope
NR43 = 0x22  # Polynomial counter
NR44 = 0x23  # Trigger

# Control
NR50 = 0x24  # Channel control / volume
NR51 = 0x25  # Output selection
NR52 = 0x26  # Sound on/off

# Frequency register pairs per channel
FREQ_LO = {1: NR13, 2: NR23, 3: NR33}
FREQ_HI = {1: NR14, 2: NR24, 3: NR34}


# ============================================
# Note frequency table
# ============================================

NOTE_NAMES = ['C-', 'C#', 'D-', 'D#', 'E-', 'F-', 'F#', 'G-', 'G#', 'A-', 'A#', 'B-']

def build_freq_table():
    """Build a table mapping hUGE note index -> GB frequency register value.
    hUGE note 0 = C-3 (130.81 Hz), note 12 = C-4, etc.
    Actually in hUGE, note values map as:
      0 = C_3, 1 = C#3, ..., 71 = B_8
    The GB freq register: freq_hz = 131072 / (2048 - freq_reg)
    """
    table = []
    # A4 = 440 Hz, MIDI note 69
    # C3 = MIDI 48
    for uge_note in range(72):  # C-3 to B-8
        midi_note = 48 + uge_note  # C3 = MIDI 48
        freq_hz = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
        freq_reg = int(round(2048 - 131072.0 / freq_hz))
        if freq_reg < 0:
            freq_reg = 0
        if freq_reg > 2047:
            freq_reg = 2047
        table.append((uge_note, freq_reg, freq_hz))
    return table

FREQ_TABLE = build_freq_table()

def freq_reg_to_uge_note(freq_reg):
    """Find the closest hUGE note for a given GB frequency register value."""
    if freq_reg <= 0 or freq_reg >= 2048:
        return NO_NOTE

    target_hz = 131072.0 / (2048 - freq_reg)

    best_note = NO_NOTE
    best_diff = float('inf')
    for uge_note, reg_val, note_hz in FREQ_TABLE:
        diff = abs(target_hz - note_hz)
        if diff < best_diff:
            best_diff = diff
            best_note = uge_note
    return best_note

def uge_note_name(note):
    """Return human-readable name for a hUGE note value."""
    if note == NO_NOTE or note < 0 or note >= 72:
        return "---"
    octave = 3 + note // 12
    semitone = note % 12
    return f"{NOTE_NAMES[semitone]}{octave}"

def noise_reg_to_uge_note(poly_reg):
    """Convert CH4 polynomial counter register to a hUGE noise 'note'.
    NR43 format: SSSS W DDD
      S = shift clock freq, W = counter width, D = dividing ratio
    hUGE maps noise notes differently -- we approximate by using the
    shift value as a rough pitch indicator.
    """
    shift = (poly_reg >> 4) & 0x0F
    width = (poly_reg >> 3) & 0x01
    divisor = poly_reg & 0x07
    # Map shift 0-15 to notes roughly. Lower shift = higher freq = higher note.
    # hUGE noise notes: 0 is highest pitch, going down.
    # This is approximate -- noise isn't tonal.
    note = min(shift * 4, 71)
    return note


# ============================================
# Dump file parser
# ============================================

# Pattern: ROM00:09D9: Write [18] = ce scanline=7 frame=223
LINE_RE = re.compile(
    r'.*Write\s+\[([0-9a-fA-F]+)\]\s*=\s*([0-9a-fA-F]+)\s+'
    r'scanline=(\d+)\s+frame=(\d+)'
)

def parse_dump(filepath):
    """Parse a dump file into a list of (frame, scanline, register, value) tuples."""
    events = []
    with open(filepath, 'r') as f:
        for line in f:
            m = LINE_RE.match(line.strip())
            if m:
                reg = int(m.group(1), 16)
                val = int(m.group(2), 16)
                scanline = int(m.group(3))
                frame = int(m.group(4))
                events.append((frame, scanline, reg, val))
    return events


def unwrap_frames(events):
    """Unwrap the 8-bit frame counter into a continuous counter.
    The frame counter wraps from 255 to 0.
    """
    if not events:
        return events

    unwrapped = []
    offset = 0
    prev_raw = events[0][0]

    for frame, scanline, reg, val in events:
        if frame < prev_raw - 128:  # Wrapped forward (0 after 255)
            offset += 256
        elif frame > prev_raw + 128:  # Wrapped backward (shouldn't happen normally)
            offset -= 256
        prev_raw = frame
        unwrapped.append((frame + offset, scanline, reg, val))

    # Normalize so first frame = 0
    min_frame = unwrapped[0][0]
    unwrapped = [(f - min_frame, s, r, v) for f, s, r, v in unwrapped]
    return unwrapped


# ============================================
# Event extraction
# ============================================

def extract_channel_events(events):
    """Process raw register writes into per-frame note events for each channel.
    
    Returns a dict: {channel: {frame: note_info}} where channel is 1-4.
    note_info has keys: 'note', 'triggered', 'volume', 'duty', etc.
    """
    # Track register state
    regs = {}
    
    # Group events by frame
    frames = defaultdict(list)
    for frame, scanline, reg, val in events:
        frames[frame].append((scanline, reg, val))
    
    # Per-channel note events: {channel: [(frame, uge_note, triggered), ...]}
    channel_notes = {1: {}, 2: {}, 3: {}, 4: {}}
    
    for frame in sorted(frames.keys()):
        frame_writes = frames[frame]
        
        # Track which channels had frequency updates this frame
        ch_freq_updated = set()
        ch_triggered = set()
        ch_noise_updated = False
        
        for scanline, reg, val in frame_writes:
            old_val = regs.get(reg, 0)
            regs[reg] = val
            
            # Check for frequency writes and triggers
            for ch in [1, 2, 3]:
                if reg == FREQ_LO[ch]:
                    ch_freq_updated.add(ch)
                elif reg == FREQ_HI[ch]:
                    ch_freq_updated.add(ch)
                    if val & 0x80:  # Trigger bit
                        ch_triggered.add(ch)
            
            # Channel 4 noise
            if reg == NR43:
                ch_freq_updated.add(4)
            elif reg == NR44:
                if val & 0x80:
                    ch_triggered.add(4)
                ch_freq_updated.add(4)
        
        # For channels that had frequency updates, record the note
        for ch in [1, 2, 3]:
            if ch in ch_freq_updated:
                lo = regs.get(FREQ_LO[ch], 0)
                hi = regs.get(FREQ_HI[ch], 0)
                freq_reg = ((hi & 0x07) << 8) | lo
                note = freq_reg_to_uge_note(freq_reg)
                triggered = ch in ch_triggered
                channel_notes[ch][frame] = {
                    'note': note,
                    'triggered': triggered,
                }
        
        if 4 in ch_freq_updated:
            poly = regs.get(NR43, 0)
            note = noise_reg_to_uge_note(poly)
            triggered = 4 in ch_triggered
            channel_notes[4][frame] = {
                'note': note,
                'triggered': triggered,
            }
    
    return channel_notes


def deduplicate_notes(channel_notes):
    """Remove consecutive duplicate notes (same note, not triggered) to keep
    only actual note changes."""
    cleaned = {1: {}, 2: {}, 3: {}, 4: {}}
    
    for ch in [1, 2, 3, 4]:
        prev_note = None
        for frame in sorted(channel_notes[ch].keys()):
            info = channel_notes[ch][frame]
            note = info['note']
            triggered = info['triggered']
            
            if note != prev_note or triggered:
                cleaned[ch][frame] = info
                prev_note = note
    
    return cleaned


# ============================================
# UGE file generation
# ============================================

def build_uge_patterns(channel_notes, ticks_per_row=1):
    """Convert frame-based note events into UGE patterns.
    
    With ticks_per_row=1, each frame = one row.
    Patterns are 64 rows each.
    
    Returns: (patterns_per_channel, pattern_order_per_channel, total_frames)
      patterns_per_channel: {ch: {pattern_id: [(row, note, instrument)]}}
      pattern_order_per_channel: {ch: [pattern_id, ...]}
    """
    # Find total frame range
    all_frames = set()
    for ch in [1, 2, 3, 4]:
        all_frames.update(channel_notes[ch].keys())
    
    if not all_frames:
        print("Warning: No note events found!")
        return {}, {}, 0
    
    max_frame = max(all_frames)
    total_rows = max_frame + 1
    num_patterns = (total_rows + 63) // 64
    
    print(f"Total frames: {total_rows}, patterns needed: {num_patterns}")
    
    # Build pattern data for each channel
    # Each pattern is identified by (channel, pattern_index)
    # We'll use a global pattern numbering
    
    patterns = {}  # pattern_id -> {ch -> [(row, note, instrument)]}
    
    # Instrument mapping: ch1 = instrument 0, ch2 = 1, ch3 = wave 0 (15), ch4 = noise 0 (30)
    ch_instrument = {1: 0, 2: 1, 3: 0, 4: 0}
    
    for pat_idx in range(num_patterns):
        pat_data = {1: [], 2: [], 3: [], 4: []}
        frame_start = pat_idx * 64
        
        for ch in [1, 2, 3, 4]:
            for row in range(64):
                frame = frame_start + row
                if frame in channel_notes[ch]:
                    info = channel_notes[ch][frame]
                    note = info['note']
                    if note != NO_NOTE:
                        pat_data[ch].append((row, note, ch_instrument[ch]))
        
        patterns[pat_idx] = pat_data
    
    return patterns, num_patterns, total_rows


def write_uge_file(channel_notes, output_path, song_name="Converted", ticks_per_row=1):
    """Write a complete .uge file from channel note events."""
    
    patterns, num_patterns, total_frames = build_uge_patterns(channel_notes, ticks_per_row)
    
    if num_patterns == 0:
        print("No patterns to write!")
        return
    
    # Cap at 255 patterns (hUGE limit)
    if num_patterns > 255:
        print(f"Warning: {num_patterns} patterns exceeds hUGE limit of 255, truncating")
        num_patterns = 255
    
    # We need one empty pattern too
    empty_pattern_id = num_patterns
    total_pattern_count = num_patterns + 1
    
    print(f"Writing {num_patterns} patterns + 1 empty = {total_pattern_count} total")
    
    with open(output_path, 'wb') as f:
        # Header
        write_uge_int(f, UGE_FORMAT_VERSION)
        write_uge_shortstring(f, song_name)
        write_uge_shortstring(f, "")  # Artist
        write_uge_shortstring(f, "Converted from register dump")
        
        # 45 Instruments (15 duty + 15 wave + 15 noise)
        
        # Duty instrument 0: CH1 Pulse
        write_uge_instrument(f, type_=0, name="CH1 Pulse", initial_volume=15, duty=2)
        # Duty instrument 1: CH2 Pulse
        write_uge_instrument(f, type_=0, name="CH2 Pulse", initial_volume=15, duty=2)
        # Duty instruments 2-14: empty
        for _ in range(13):
            write_uge_instrument(f, type_=0)
        
        # Wave instrument 0: CH3 Wave
        write_uge_instrument(f, type_=1, name="CH3 Wave", output_level=1)
        # Wave instruments 1-14: empty
        for _ in range(14):
            write_uge_instrument(f, type_=1)
        
        # Noise instrument 0: CH4 Noise
        write_uge_instrument(f, type_=2, name="CH4 Noise", initial_volume=15)
        # Noise instruments 1-14: empty
        for _ in range(14):
            write_uge_instrument(f, type_=2)
        
        # 16 Waves (32 bytes each)
        # Wave 0: Triangle
        triangle = list(range(16)) + list(range(15, -1, -1))
        f.write(bytes(triangle))
        # Wave 1: Square 50%
        f.write(bytes([0]*16 + [15]*16))
        # Wave 2: Sawtooth
        f.write(bytes([i % 16 for i in range(32)]))
        # Waves 3-15: silence
        for _ in range(13):
            f.write(bytes(32))
        
        # Timing
        write_uge_int(f, ticks_per_row)
        f.write(bytes([0]))    # TimerEnabled = False
        write_uge_int(f, 0)    # TimerDivider
        
        # Patterns
        write_uge_int(f, total_pattern_count)
        
        # Write each pattern -- in UGE, each "pattern" is per-channel,
        # but in the file format, a pattern_key contains data for ONE channel
        # and the order matrix assigns pattern keys to channels.
        #
        # Actually, looking at generate_song.py more carefully:
        # Each pattern key = 64 cells for ONE channel.
        # The order matrix maps pattern keys per channel.
        #
        # So we need separate pattern keys for each channel.
        # pattern key layout:
        #   CH1 patterns: 0 .. num_patterns-1  (melody patterns for ch1)
        #   CH2 patterns: num_patterns .. 2*num_patterns-1
        #   CH3 patterns: 2*num_patterns .. 3*num_patterns-1
        #   CH4 patterns: 3*num_patterns .. 4*num_patterns-1
        #   Empty pattern: 4*num_patterns
        
        # Recalculate
        total_pattern_keys = num_patterns * 4 + 1  # 4 channels + 1 empty
        
        # Rewrite the count
        f.seek(f.tell() - 4)
        write_uge_int(f, total_pattern_keys)
        
        # Write CH1 patterns
        for pat_idx in range(num_patterns):
            key = pat_idx
            write_uge_int(f, key)
            pat = patterns.get(pat_idx, {})
            ch_notes = {row: (note, inst) for row, note, inst in pat.get(1, [])}
            for row in range(64):
                if row in ch_notes:
                    note, inst = ch_notes[row]
                    write_uge_cell(f, note=note, instrument=inst + 1)
                else:
                    write_uge_cell(f)
        
        # Write CH2 patterns
        for pat_idx in range(num_patterns):
            key = num_patterns + pat_idx
            write_uge_int(f, key)
            pat = patterns.get(pat_idx, {})
            ch_notes = {row: (note, inst) for row, note, inst in pat.get(2, [])}
            for row in range(64):
                if row in ch_notes:
                    note, inst = ch_notes[row]
                    write_uge_cell(f, note=note, instrument=inst + 1)
                else:
                    write_uge_cell(f)
        
        # Write CH3 patterns
        for pat_idx in range(num_patterns):
            key = 2 * num_patterns + pat_idx
            write_uge_int(f, key)
            pat = patterns.get(pat_idx, {})
            ch_notes = {row: (note, inst) for row, note, inst in pat.get(3, [])}
            for row in range(64):
                if row in ch_notes:
                    note, inst = ch_notes[row]
                    write_uge_cell(f, note=note, instrument=inst + 1)
                else:
                    write_uge_cell(f)
        
        # Write CH4 patterns
        for pat_idx in range(num_patterns):
            key = 3 * num_patterns + pat_idx
            write_uge_int(f, key)
            pat = patterns.get(pat_idx, {})
            ch_notes = {row: (note, inst) for row, note, inst in pat.get(4, [])}
            for row in range(64):
                if row in ch_notes:
                    note, inst = ch_notes[row]
                    write_uge_cell(f, note=note, instrument=inst + 1)
                else:
                    write_uge_cell(f)
        
        # Empty pattern
        empty_key = 4 * num_patterns
        write_uge_int(f, empty_key)
        for _ in range(64):
            write_uge_cell(f)
        
        # Order matrix (4 channels)
        order_len = num_patterns + 1  # +1 for loop-back entry
        
        # CH1 order
        write_uge_int(f, order_len)
        for i in range(num_patterns):
            write_uge_int(f, i)  # CH1 pattern keys
        write_uge_int(f, 0)  # Loop to beginning
        
        # CH2 order
        write_uge_int(f, order_len)
        for i in range(num_patterns):
            write_uge_int(f, num_patterns + i)
        write_uge_int(f, 0)
        
        # CH3 order
        write_uge_int(f, order_len)
        for i in range(num_patterns):
            write_uge_int(f, 2 * num_patterns + i)
        write_uge_int(f, 0)
        
        # CH4 order
        write_uge_int(f, order_len)
        for i in range(num_patterns):
            write_uge_int(f, 3 * num_patterns + i)
        write_uge_int(f, 0)
        
        # 16 Routines (all empty)
        for _ in range(16):
            write_uge_int(f, 0)
    
    import os
    file_size = os.path.getsize(output_path)
    print(f"Written: {output_path} ({file_size} bytes)")


def print_summary(channel_notes, max_frames=20):
    """Print a summary of the first N frames of note events."""
    all_frames = set()
    for ch in [1, 2, 3, 4]:
        all_frames.update(channel_notes[ch].keys())
    
    if not all_frames:
        print("No events found.")
        return
    
    print(f"\nFrame range: {min(all_frames)} - {max(all_frames)}")
    print(f"Events per channel: CH1={len(channel_notes[1])}, CH2={len(channel_notes[2])}, "
          f"CH3={len(channel_notes[3])}, CH4={len(channel_notes[4])}")
    
    print(f"\nFirst {max_frames} frames with events:")
    print(f"{'Frame':>6}  {'CH1':>8}  {'CH2':>8}  {'CH3':>8}  {'CH4':>8}")
    print("-" * 50)
    
    count = 0
    for frame in sorted(all_frames):
        if count >= max_frames:
            break
        
        cols = []
        has_event = False
        for ch in [1, 2, 3, 4]:
            if frame in channel_notes[ch]:
                info = channel_notes[ch][frame]
                name = uge_note_name(info['note'])
                trig = "T" if info['triggered'] else " "
                cols.append(f"{name}{trig}")
                has_event = True
            else:
                cols.append("   ---  ")
        
        if has_event:
            print(f"{frame:>6}  {'  '.join(f'{c:>8}' for c in cols)}")
            count += 1


def convert_dump(input_path, output_path, song_name=None, ticks_per_row=1):
    """Main conversion pipeline."""
    if song_name is None:
        song_name = input_path.rsplit('/', 1)[-1].rsplit('.', 1)[0]
    
    print(f"Parsing {input_path}...")
    events = parse_dump(input_path)
    print(f"  {len(events)} register writes found")
    
    print("Unwrapping frame counter...")
    events = unwrap_frames(events)
    
    print("Extracting channel events...")
    channel_notes = extract_channel_events(events)
    
    print("Deduplicating consecutive same-notes...")
    channel_notes = deduplicate_notes(channel_notes)
    
    print_summary(channel_notes)
    
    print(f"\nWriting .uge file: {output_path}")
    write_uge_file(channel_notes, output_path, song_name=song_name,
                   ticks_per_row=ticks_per_row)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert GB sound register dumps to .uge')
    parser.add_argument('input', help='Input dump file (.txt)')
    parser.add_argument('-o', '--output', help='Output .uge file (default: input with .uge extension)')
    parser.add_argument('-n', '--name', help='Song name', default=None)
    parser.add_argument('-t', '--ticks', type=int, default=1,
                        help='Ticks per row (default: 1, each frame = 1 row)')
    args = parser.parse_args()
    
    output = args.output
    if output is None:
        output = args.input.rsplit('.', 1)[0] + '.uge'
    
    convert_dump(args.input, output, song_name=args.name, ticks_per_row=args.ticks)
