#!/usr/bin/env python3
"""
PHANTOM DASH - A ghastly rhythm game track for Game Boy
Generates a .uge file (hUGE Tracker V6 format)

Structure:
  Echo Intro (quiet whisper of main theme) →
  Intro (drums build) → Section A (driving C minor) →
  Ghostly Interlude 1 → Section B (escalated, Eb shifted) →
  Ghostly Interlude 2 → Section C (climax) →
  Breakdown w/ ghosts → Final drop → Ghostly outro

Key: C minor (C D Eb F G Ab Bb)
Tempo: ~149 BPM (ticks_per_row=3, 8 rows per beat)
"""

import struct

# ============================================
# .uge format constants
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
    for _ in range(64):
        write_uge_cell(f)


# ============================================
# Musical constants
# ============================================

# C minor scale hUGE note values (note 0 = C-3)
# Octave 3
C3, D3, Eb3, F3, G3, Ab3, Bb3 = 0, 2, 3, 5, 7, 8, 10
# Octave 4
C4, D4, Eb4, F4, G4, Ab4, Bb4 = 12, 14, 15, 17, 19, 20, 22
# Octave 5
C5, D5, Eb5, F5, G5, Ab5, Bb5 = 24, 26, 27, 29, 31, 32, 34
# Octave 6
C6, D6, Eb6, F6, G6 = 36, 38, 39, 41, 43
# Octave 7
C7, D7, Eb7 = 48, 50, 51
# Chromatic helpers
Cs3, Cs4, Cs5 = 1, 13, 25  # C#
B3, B4, B5 = 11, 23, 35
A3, A4, A5 = 9, 21, 33
E3, E4, E5 = 4, 16, 28
Fs3, Fs4 = 6, 18
Gs3, Gs4 = 8, 20

# Noise "notes" for percussion (lower number = higher freq)
HIHAT = 4       # High, ticky
HIHAT_OPEN = 8  # Slightly lower, open feel
SNARE = 18      # Mid, snappy
KICK = 36       # Low, boomy
TOM_HI = 24     # Tom sounds
TOM_LO = 30

# hUGE effects
EFF_ARP = 0        # 0xy: arpeggio
EFF_PORTUP = 1     # 1xx: portamento up
EFF_PORTDN = 2     # 2xx: portamento down
EFF_VIBRATO = 4    # 4xy: vibrato
EFF_SETMASTER = 5  # 5xx: set master volume
EFF_CALLRTN = 6    # 6xx: call routine
EFF_NOTEOFF = 7    # 7xx: note delay (delayed note cut)
EFF_PANNING = 8    # 8xx: set panning
EFF_DUTY = 9       # 9xx: set duty cycle
EFF_VOLSLIDE = 10  # Axy: volume slide
EFF_POSJUMP = 11   # Bxx: position jump
EFF_SETVOL = 12    # Cxx: set volume
EFF_PATBREAK = 13  # Dxx: pattern break
EFF_NOTECUT = 14   # Exx: note cut (after xx ticks)
EFF_SPEED = 15     # Fxx: set speed


# ============================================
# Pattern builder
# ============================================

class Pattern:
    """Build a 64-row pattern for one channel."""
    def __init__(self):
        self.cells = {}  # row -> (note, instrument, volume, effect_code, effect_params)
    
    def note(self, row, note, instrument=0, volume=0, effect_code=0, effect_params=0):
        """Place a note at a specific row."""
        if 0 <= row < 64:
            self.cells[row] = (note, instrument, volume, effect_code, effect_params)
        return self
    
    def arp(self, row, base_note, semitones_up, instrument=0):
        """Place a note with arpeggio effect."""
        return self.note(row, base_note, instrument, 
                        effect_code=EFF_ARP, effect_params=(semitones_up << 4))
    
    def cut(self, row, after_ticks=0):
        """Note cut at row."""
        return self.note(row, NO_NOTE, effect_code=EFF_NOTECUT, effect_params=after_ticks)
    
    def vol(self, row, note, instrument, volume):
        """Place a note with volume."""
        return self.note(row, note, instrument, effect_code=EFF_SETVOL, effect_params=volume)

    def write(self, f, key):
        """Write this pattern to the file."""
        write_uge_int(f, key)
        for row in range(64):
            if row in self.cells:
                n, i, v, ec, ep = self.cells[row]
                write_uge_cell(f, note=n, instrument=i, volume=v,
                              effect_code=ec, effect_params=ep)
            else:
                write_uge_cell(f)


def empty_pattern():
    return Pattern()


# ============================================
# Drum patterns
# ============================================

def drums_buildup_1():
    """Sparse hi-hats only, building tension."""
    p = Pattern()
    # Hi-hats on off-beats, getting denser
    for row in [8, 24, 40, 56]:  # Start sparse
        p.note(row, HIHAT, instrument=1)
    return p

def drums_buildup_2():
    """Hi-hats + kick enters."""
    p = Pattern()
    for row in range(0, 64, 8):  # Hi-hat every beat
        p.note(row, HIHAT, instrument=1)
    for row in [0, 16, 32, 48]:  # Kick on 1 and 3
        p.note(row, KICK, instrument=3)
    return p

def drums_main():
    """Standard driving drum pattern."""
    p = Pattern()
    # Hi-hat: 8th notes
    for row in range(0, 64, 4):
        p.note(row, HIHAT, instrument=1)
    # Kick: 1 and 3
    for row in [0, 16, 32, 48]:
        p.note(row, KICK, instrument=3)
    # Snare: 2 and 4
    for row in [8, 24, 40, 56]:
        p.note(row, SNARE, instrument=2)
    return p

def drums_intense():
    """Intense drums with 16th hi-hats and syncopation."""
    p = Pattern()
    # Hi-hat: 16th notes
    for row in range(0, 64, 2):
        p.note(row, HIHAT, instrument=1)
    # Kick: syncopated
    for row in [0, 6, 16, 22, 32, 38, 48, 54]:
        p.note(row, KICK, instrument=3)
    # Snare: 2 and 4 with ghost notes
    for row in [8, 24, 40, 56]:
        p.note(row, SNARE, instrument=2)
    for row in [4, 20, 36, 52]:
        p.vol(row, SNARE, instrument=2, volume=4)  # ghost snare
    return p

def drums_climax():
    """Maximum intensity: fills, double kicks."""
    p = Pattern()
    # Hi-hat: 16ths
    for row in range(0, 64, 2):
        p.note(row, HIHAT, instrument=1)
    # Double kick
    for row in [0, 2, 16, 18, 32, 34, 48, 50]:
        p.note(row, KICK, instrument=3)
    # Snare with rolls
    for row in [8, 10, 24, 26, 40, 42, 56, 58]:
        p.note(row, SNARE, instrument=2)
    return p

def drums_sparse_ghost():
    """Sparse, ghostly drums - just a distant pulse."""
    p = Pattern()
    for row in [0, 32]:
        p.note(row, KICK, instrument=3)
    for row in [16, 48]:
        p.vol(row, HIHAT, instrument=1, volume=4)
    return p

def drums_fill():
    """Drum fill for transitions."""
    p = Pattern()
    # Normal first half
    for row in range(0, 32, 4):
        p.note(row, HIHAT, instrument=1)
    for row in [0, 16]:
        p.note(row, KICK, instrument=3)
    for row in [8, 24]:
        p.note(row, SNARE, instrument=2)
    # Fill in second half: rapid toms and snares
    fill_notes = [TOM_HI, SNARE, TOM_LO, SNARE, TOM_HI, TOM_LO, SNARE, SNARE,
                  TOM_HI, SNARE, TOM_LO, SNARE, KICK, SNARE, KICK, KICK]
    for i, row in enumerate(range(32, 64, 2)):
        inst = 2 if fill_notes[i] == SNARE else 3
        p.note(row, fill_notes[i], instrument=inst)
    return p

def drums_halftime():
    """Half-time feel for breakdown."""
    p = Pattern()
    for row in [0, 32]:
        p.note(row, KICK, instrument=3)
    for row in [16, 48]:
        p.note(row, SNARE, instrument=2)
    for row in range(0, 64, 8):
        p.note(row, HIHAT, instrument=1)
    return p


# ============================================
# Bass patterns (CH3 - Wave)
# ============================================

def bass_cminor_drive():
    """Driving C minor bass: C C C C Ab Ab G G (octave pulses)."""
    p = Pattern()
    bass = [(0, C3), (4, C4), (8, C3), (12, C4),
            (16, C3), (20, C4), (24, C3), (28, C4),
            (32, Ab3), (36, Ab3), (40, Ab3), (44, Ab3),
            (48, G3), (52, G3), (56, G3), (60, G3)]
    for row, note in bass:
        p.note(row, note, instrument=1)
    return p

def bass_cminor_groove():
    """Groovy C minor bass with rests."""
    p = Pattern()
    bass = [(0, C3), (4, C3), (6, Eb3), (8, G3),
            (14, C3), (16, C3), (20, C3), (22, Eb3),
            (24, F3), (30, C3),
            (32, Ab3), (36, Ab3), (38, G3), (40, F3),
            (44, Eb3), (48, G3), (52, G3), (54, F3),
            (56, Eb3), (60, D3)]
    for row, note in bass:
        p.note(row, note, instrument=1)
    return p

def bass_ebminor_drive():
    """Shifted to Eb minor for Section B."""
    p = Pattern()
    bass = [(0, Eb3), (4, Eb4), (8, Eb3), (12, Eb4),
            (16, Eb3), (20, Eb4), (24, Eb3), (28, Eb4),
            (32, B3), (36, B3), (40, B3), (44, B3),
            (48, Bb3), (52, Bb3), (56, Bb3), (60, Bb3)]
    for row, note in bass:
        p.note(row, note, instrument=1)
    return p

def bass_climax():
    """Climax bass: relentless 8ths."""
    p = Pattern()
    notes = [C3, C3, Eb3, Eb3, G3, G3, C4, C4,
             Ab3, Ab3, G3, G3, F3, F3, G3, G3,
             C3, C3, Eb3, Eb3, G3, G3, Bb3, Bb3,
             Ab3, Ab3, G3, G3, F3, Eb3, D3, C3]
    for i, note in enumerate(notes):
        p.note(i * 2, note, instrument=1)
    return p

def bass_ghost_hold():
    """Ghostly interlude bass: just root drones."""
    p = Pattern()
    p.note(0, C3, instrument=1)
    p.note(32, G3, instrument=1)
    return p

def bass_breakdown():
    """Half-time breakdown bass."""
    p = Pattern()
    bass = [(0, C3), (16, Eb3), (32, Ab3), (48, G3)]
    for row, note in bass:
        p.note(row, note, instrument=1)
    return p


# ============================================
# Lead melody patterns (CH1 - Pulse)
# ============================================

def lead_silent():
    return empty_pattern()

def lead_main_A1():
    """Main theme part 1: rising C minor melody."""
    p = Pattern()
    melody = [(0, C5), (6, Eb5), (8, G5), (12, Eb5),
              (14, F5), (16, G5), (22, Ab5), (24, G5),
              (28, F5), (30, Eb5),
              (32, Ab5), (36, G5), (38, F5), (40, Eb5),
              (44, D5), (46, C5), (48, Eb5), (52, D5),
              (54, C5), (56, Bb4), (60, C5)]
    for row, note in melody:
        p.note(row, note, instrument=1)
    return p

def lead_main_A2():
    """Main theme part 2: answering phrase."""
    p = Pattern()
    melody = [(0, G5), (4, Ab5), (6, Bb5), (8, C6),
              (14, Bb5), (16, Ab5), (20, G5),
              (24, F5), (28, Eb5), (30, F5),
              (32, G5), (36, Ab5), (38, Bb5), (40, C6),
              (44, Bb5), (46, Ab5), (48, G5),
              (52, F5), (56, Eb5), (60, D5)]
    for row, note in melody:
        p.note(row, note, instrument=1)
    return p

def lead_main_A3():
    """Variation: syncopated, more aggressive."""
    p = Pattern()
    melody = [(0, C5), (2, Eb5), (4, G5), (8, C6),
              (10, Bb5), (14, Ab5), (16, G5),
              (18, Ab5), (20, G5), (22, F5),
              (24, Eb5), (26, G5), (28, Bb5),
              (32, Ab5), (34, G5), (38, F5),
              (40, Eb5), (42, F5), (44, G5),
              (48, C5), (50, D5), (52, Eb5),
              (54, F5), (56, G5), (58, Ab5),
              (60, Bb5), (62, C6)]
    for row, note in melody:
        p.note(row, note, instrument=1)
    return p

def lead_main_A4():
    """Variation: descending runs."""
    p = Pattern()
    melody = [(0, C6), (2, Bb5), (4, Ab5), (6, G5),
              (8, F5), (10, Eb5), (12, D5), (14, C5),
              (16, Eb5), (20, G5), (24, C6),
              (28, Bb5), (30, Ab5),
              (32, G5), (34, F5), (36, Eb5), (38, D5),
              (40, C5), (42, D5), (44, Eb5), (46, F5),
              (48, G5), (52, Ab5), (56, G5),
              (60, Eb5)]
    for row, note in melody:
        p.note(row, note, instrument=1)
    return p

def lead_B1():
    """Section B: Eb minor, more intense."""
    p = Pattern()
    # Eb minor: Eb F Gb Ab Bb Cb(B) Db
    Gb4 = 18  # F#4
    Db5 = 25  # C#5
    Gb5 = 30  # F#5
    Cb5 = 35  # B5
    melody = [(0, Eb5), (2, Gb5), (4, Bb5), (8, Eb6),
              (10, Db5+12), (14, Cb5), (16, Bb5),
              (18, Ab5), (20, Gb5), (24, Eb5),
              (28, Bb5), (30, Ab5),
              (32, Gb5), (34, Ab5), (36, Bb5), (38, Eb5+12),
              (40, Db5+12), (44, Cb5), (46, Bb5),
              (48, Ab5), (50, Gb5), (52, Eb5),
              (56, Bb4), (58, Eb5), (60, Gb5), (62, Bb5)]
    for row, note in melody:
        if note < 72:
            p.note(row, note, instrument=1)
    return p

def lead_B2():
    """Section B part 2: even more intense runs."""
    p = Pattern()
    Gb5 = 30
    Cb5 = 35
    melody = [(0, Bb5), (1, Ab5), (2, Gb5), (3, Eb5),
              (4, Bb5), (5, Ab5), (6, Gb5), (7, Eb5),
              (8, Bb5), (10, Eb5+12), (12, Bb5),
              (16, Ab5), (17, Gb5), (18, Eb5), (19, Ab5),
              (20, Gb5), (21, Eb5), (22, Gb5), (23, Ab5),
              (24, Bb5), (28, Eb5),
              (32, Gb5), (33, Ab5), (34, Bb5), (35, Ab5),
              (36, Gb5), (37, Eb5), (38, Gb5), (39, Bb5),
              (40, Eb5+12), (44, Bb5), (48, Ab5),
              (52, Gb5), (54, Eb5), (56, Bb4),
              (58, Eb5), (60, Gb5), (62, Ab5)]
    for row, note in melody:
        if note < 72:
            p.note(row, note, instrument=1)
    return p

def lead_climax_1():
    """Climax: rapid arpeggiated C minor. Intense."""
    p = Pattern()
    # Rapid ascending/descending C minor arpeggios
    arp_up = [C5, Eb5, G5, C6, Eb5+12, G5, C6, Eb5+12]
    for i in range(8):
        n = arp_up[i % len(arp_up)]
        if n < 72:
            p.note(i, n, instrument=1)
    # Descending
    arp_dn = [C6, G5, Eb5, C5, G4, Eb4, C4, Eb4]
    for i in range(8):
        n = arp_dn[i % len(arp_dn)]
        p.note(8 + i, n, instrument=1)
    # Repeat with variation
    arp2 = [Ab5, G5, F5, Eb5, D5, C5, Bb4, C5,
            Eb5, F5, G5, Ab5, Bb5, C6, Bb5, Ab5]
    for i in range(16):
        n = arp2[i]
        if n < 72:
            p.note(16 + i, n, instrument=1)
    # Second half: sustained power notes with arpeggio effect
    p.arp(32, C5, 7, instrument=1)   # C+G arp
    p.arp(40, Ab4, 7, instrument=1)  # Ab+Eb arp
    p.arp(48, Bb4, 5, instrument=1)  # Bb+Eb arp
    p.arp(56, G4, 5, instrument=1)   # G+C arp
    return p

def lead_climax_2():
    """Climax part 2: peak energy."""
    p = Pattern()
    # Stabbing chords via arpeggios
    for row in range(0, 32, 4):
        notes_cycle = [(C5, 3), (Eb5, 3), (G5, 3), (Ab5, 4),
                       (G5, 3), (F5, 2), (Eb5, 3), (C5, 7)]
        base, arp = notes_cycle[(row // 4) % len(notes_cycle)]
        p.arp(row, base, arp, instrument=1)
    # Rapid scale run to end
    run = [C5, D5, Eb5, F5, G5, Ab5, Bb5, C6,
           Bb5, Ab5, G5, F5, Eb5, D5, C5, D5,
           Eb5, F5, G5, Ab5, Bb5, C6, Bb5, Ab5,
           G5, Ab5, Bb5, C6, Bb5, C6, Bb5, C6]
    for i, note in enumerate(run):
        if note < 72:
            p.note(32 + i, note, instrument=1)
    return p


# ============================================
# Harmony patterns (CH2 - Pulse)
# ============================================

def harmony_silent():
    return empty_pattern()

def harmony_A1():
    """Counter-melody supporting Section A."""
    p = Pattern()
    melody = [(0, Eb4), (8, G4), (16, C5), (20, Bb4),
              (24, Ab4), (28, G4),
              (32, F4), (36, Ab4), (40, G4),
              (48, Eb4), (52, F4), (56, G4)]
    for row, note in melody:
        p.note(row, note, instrument=2)
    return p

def harmony_A2():
    """Second harmony pattern."""
    p = Pattern()
    melody = [(0, Eb5), (8, D5), (16, C5), (20, Bb4),
              (24, Ab4), (28, Bb4),
              (32, C5), (36, Bb4), (40, Ab4),
              (48, G4), (52, Ab4), (56, Bb4)]
    for row, note in melody:
        p.note(row, note, instrument=2)
    return p

def harmony_B1():
    """Section B harmony: Eb minor support."""
    p = Pattern()
    Gb4 = 18
    melody = [(0, Eb4), (8, Gb4), (16, Bb4), (24, Ab4),
              (32, Gb4), (40, Eb4), (48, Bb4), (56, Ab4)]
    for row, note in melody:
        p.note(row, note, instrument=2)
    return p

def harmony_climax():
    """Climax harmony: arpeggiated power chords."""
    p = Pattern()
    p.arp(0, Eb4, 3, instrument=2)   # Eb minor
    p.arp(8, Ab4, 4, instrument=2)   # Ab major
    p.arp(16, Bb4, 3, instrument=2)  # Bb minor
    p.arp(24, G4, 3, instrument=2)   # G minor
    p.arp(32, C4, 3, instrument=2)   # C minor
    p.arp(40, F4, 3, instrument=2)   # F minor
    p.arp(48, Ab4, 4, instrument=2)  # Ab major
    p.arp(56, G4, 5, instrument=2)   # G -> C
    return p

def harmony_breakdown():
    """Sparse breakdown chords."""
    p = Pattern()
    p.note(0, Eb4, instrument=2)
    p.note(24, G4, instrument=2)
    p.note(32, Ab4, instrument=2)
    p.note(48, Bb4, instrument=2)
    return p


# ============================================
# Ghostly interlude patterns (using captured data)
# ============================================

def ghostly_arp_low():
    """Phase 1: A#3 <-> B-3 oscillation via arpeggio. Eerie low tremolo."""
    p = Pattern()
    # A#3=10, B-3=11, diff=1
    for row in range(0, 64, 2):
        p.arp(row, Bb3, 1, instrument=3)  # Bb <-> B arpeggio
    return p

def ghostly_arp_mid():
    """Phase 2: C-3 <-> D-3 oscillation. Deeper."""
    p = Pattern()
    for row in range(0, 64, 2):
        p.arp(row, C3, 2, instrument=3)  # C <-> D arpeggio
    return p

def ghostly_arp_high():
    """Phase 3: D-7 <-> D#7 oscillation. High-pitched eerie."""
    p = Pattern()
    for row in range(0, 64, 2):
        p.arp(row, D7, 1, instrument=3)  # D7 <-> D#7
    return p

def ghostly_arp_sweep():
    """Ghostly sweep: starts low, goes high, back to low."""
    p = Pattern()
    # Low phase (rows 0-15)
    for row in range(0, 16, 2):
        p.arp(row, Bb3, 1, instrument=3)
    # Mid phase (rows 16-31)
    for row in range(16, 32, 2):
        p.arp(row, C3, 2, instrument=3)
    # High phase (rows 32-47)
    for row in range(32, 48, 2):
        p.arp(row, D7, 1, instrument=3)
    # Return to low (rows 48-63)
    for row in range(48, 64, 2):
        p.arp(row, Bb3, 1, instrument=3)
    return p

def ghostly_dual_A():
    """For dual-channel mode: even frames on CH1."""
    p = Pattern()
    # Alternate between Bb3 and C3 phases
    for row in range(0, 32):
        p.note(row, Bb3, instrument=3)
    for row in range(32, 64):
        p.note(row, C3, instrument=3)
    return p

def ghostly_dual_B():
    """For dual-channel mode: odd frames on CH2 (offset notes)."""
    p = Pattern()
    for row in range(0, 32):
        p.note(row, B3, instrument=3)
    for row in range(32, 64):
        p.note(row, D3, instrument=3)
    return p




# ============================================
# BITTERSWEET INTERLUDE - C Major with borrowed minor
# Same melodic contour as Section A, mostly major but
# Ab (minor 6th) and Bb (minor 7th) creep in.
# It ALMOST sounds happy, but something's not right.
# ============================================

def lead_bittersweet_A1():
    """Starts major, but Ab and Bb leak through like a memory."""
    p = Pattern()
    melody = [(0, C5), (6, E5), (8, G5), (12, E5),
              (14, F5), (16, G5), (22, Ab5), (24, G5),  # Ab! not A
              (28, F5), (30, E5),
              (32, A5), (36, G5), (38, F5), (40, E5),   # A here -- brief real hope
              (44, D5), (46, C5), (48, E5), (52, D5),
              (54, C5), (56, Bb4), (60, C5)]             # Bb -- can't let go
    for row, note in melody:
        p.note(row, note, instrument=1)
    return p

def lead_bittersweet_A2():
    """Answering phrase. More major notes but the phrase endings droop."""
    p = Pattern()
    melody = [(0, G5), (4, A5), (6, B5), (8, C6),       # Bright opening!
              (14, B5), (16, Ab5), (20, G5),              # Ab instead of A on descent
              (24, F5), (28, E5), (30, F5),
              (32, G5), (36, A5), (38, Bb5), (40, C6),   # Bb sneaks in before C
              (44, Bb5), (46, Ab5), (48, G5),             # Both flats -- sinking
              (52, F5), (56, E5), (60, D5)]               # E saves it, but barely
    for row, note in melody:
        p.note(row, note, instrument=1)
    return p

def lead_bittersweet_A3():
    """The most hopeful pattern -- but ends ambiguously."""
    p = Pattern()
    melody = [(0, C5), (2, E5), (4, G5), (8, C6),
              (10, B5), (14, A5), (16, G5),               # Genuine major run
              (18, Ab5), (20, G5), (22, F5),              # Ab -- a flinch
              (24, E5), (26, G5), (28, B5),               # Recovery
              (32, Ab5), (34, G5), (38, F5),              # Ab again
              (40, E5), (42, F5), (44, G5),
              (48, C5), (50, D5), (52, Eb5),              # Eb! minor 3rd returns
              (54, F5), (56, G5), (58, Ab5),              # Ab -- sadness wins
              (60, Bb5), (62, C6)]                        # Bb->C ambiguous resolve
    for row, note in melody:
        p.note(row, note, instrument=1)
    return p

def lead_bittersweet_darken():
    """The light fades. Starts bittersweet, ends fully minor."""
    p = Pattern()
    melody = [(0, C6), (4, B5), (8, A5), (12, G5),
              (16, E5), (20, G5), (24, Ab5),              # Ab -- the first crack
              (28, G5)]
    darken = [(32, A5), (34, Ab5),                        # A crumbles to Ab
              (36, G5), (40, F5),
              (44, E5), (46, Eb5),                        # E gives way to Eb
              (48, D5), (50, C5),
              (52, Eb5), (54, F5),                        # Fully minor now
              (56, G5), (58, Ab5),
              (60, Bb4), (62, C5)]                        # Minor cadence
    for row, note in melody + darken:
        p.note(row, note, instrument=1)
    return p

def harmony_bittersweet_A1():
    """Harmony with major/minor tension. E and Ab coexist."""
    p = Pattern()
    melody = [(0, E4), (8, G4), (16, C5), (20, B4),
              (24, Ab4), (28, G4),                        # Ab in harmony
              (32, F4), (36, Ab4), (40, G4),              # Ab again
              (48, E4), (52, F4), (56, G4)]               # E -- still trying
    for row, note in melody:
        p.note(row, note, instrument=2)
    return p

def harmony_bittersweet_A2():
    """Second harmony -- more resigned."""
    p = Pattern()
    melody = [(0, E5), (8, D5), (16, C5), (20, Bb4),     # Bb not B
              (24, Ab4), (28, Bb4),                       # Ab and Bb together
              (32, C5), (36, B4), (40, Ab4),              # B then Ab -- torn
              (48, G4), (52, Ab4), (56, Bb4)]             # All minor at the end
    for row, note in melody:
        p.note(row, note, instrument=2)
    return p

def harmony_bittersweet_darken():
    """Harmony that gives up the major fight."""
    p = Pattern()
    p.note(0, E4, instrument=2)     # Last E natural
    p.note(8, G4, instrument=2)
    p.note(16, Ab4, instrument=2)   # Ab takes over
    p.note(24, G4, instrument=2)
    p.note(32, Ab4, instrument=2)
    p.note(40, Eb4, instrument=2)   # E->Eb. It's over.
    p.note(48, Ab4, instrument=2)
    p.note(56, G4, instrument=2)
    return p

def bass_bittersweet_drive():
    """Bass that's mostly major but the Ab gives it away."""
    p = Pattern()
    bass = [(0, C3), (4, C4), (8, C3), (12, C4),
            (16, C3), (20, C4), (24, C3), (28, C4),
            (32, Ab3), (36, Ab3), (40, Ab3), (44, Ab3),  # Ab not A -- the tell
            (48, G3), (52, G3), (56, G3), (60, G3)]
    for row, note in bass:
        p.note(row, note, instrument=1)
    return p

def bass_bittersweet_groove():
    """Groovy but unsettled bass. E major 3rd with Ab 6th."""
    p = Pattern()
    bass = [(0, C3), (4, C3), (6, E3), (8, G3),          # E! hopeful
            (14, C3), (16, C3), (20, C3), (22, E3),
            (24, F3), (30, C3),
            (32, Ab3), (36, Ab3), (38, G3), (40, F3),    # Ab -- nope
            (44, E3), (48, G3), (52, G3), (54, F3),
            (56, Eb3), (60, D3)]                          # Eb at the very end
    for row, note in bass:
        p.note(row, note, instrument=1)
    return p

def bass_darken():
    """Bass that transitions from bittersweet to fully minor."""
    p = Pattern()
    bass = [(0, C3), (4, C4), (8, C3), (12, E3),
            (16, G3), (20, Ab3), (24, G3), (28, E3),     # Ab already present
            (32, Ab3), (36, Ab3),                         # Leaning minor
            (40, G3), (44, F3),
            (48, Eb3), (52, D3),                          # Fully minor
            (56, C3), (60, G3)]
    for row, note in bass:
        p.note(row, note, instrument=1)
    return p

def drums_bittersweet():
    """Slightly lighter drums but not fully bouncy. Wistful."""
    p = Pattern()
    for row in range(0, 64, 4):
        p.note(row, HIHAT, instrument=1)
    for row in [0, 16, 32, 48]:
        p.note(row, KICK, instrument=3)
    for row in [8, 24, 40, 56]:
        p.vol(row, SNARE, instrument=2, volume=8)  # Quieter snare -- holding back
    return p

def drums_darken_fill():
    """Drum fill that gets heavier, transitioning back to dark."""
    p = Pattern()
    for row in range(0, 32, 4):
        p.note(row, HIHAT, instrument=1)
    for row in [0, 16]:
        p.note(row, KICK, instrument=3)
    for row in [8, 24]:
        p.vol(row, SNARE, instrument=2, volume=8)
    fill = [(32, TOM_HI), (34, TOM_HI), (36, SNARE), (38, TOM_LO),
            (40, TOM_LO), (42, SNARE), (44, KICK), (46, SNARE),
            (48, KICK), (49, KICK), (50, SNARE), (51, SNARE),
            (52, KICK), (53, KICK), (54, KICK), (55, SNARE),
            (56, KICK), (57, KICK), (58, KICK), (59, KICK),
            (60, KICK), (61, KICK), (62, KICK), (63, KICK)]
    for row, note in fill:
        inst = 2 if note == SNARE else 3
        p.note(row, note, instrument=inst)
    return p


# ============================================
# Echo intro patterns - ghostly whisper of the main theme
# ============================================

def lead_echo_A1():
    """Main theme A1 played at whisper volume, like a distant memory."""
    p = Pattern()
    melody = [(0, C5), (6, Eb5), (8, G5), (12, Eb5),
              (14, F5), (16, G5), (22, Ab5), (24, G5),
              (28, F5), (30, Eb5),
              (32, Ab5), (36, G5), (38, F5), (40, Eb5),
              (44, D5), (46, C5), (48, Eb5), (52, D5),
              (54, C5), (56, Bb4), (60, C5)]
    for row, note in melody:
        p.vol(row, note, instrument=1, volume=3)
    return p

def lead_echo_A2():
    """Main theme A2 at whisper volume."""
    p = Pattern()
    melody = [(0, G5), (4, Ab5), (6, Bb5), (8, C6),
              (14, Bb5), (16, Ab5), (20, G5),
              (24, F5), (28, Eb5), (30, F5),
              (32, G5), (36, Ab5), (38, Bb5), (40, C6),
              (44, Bb5), (46, Ab5), (48, G5),
              (52, F5), (56, Eb5), (60, D5)]
    for row, note in melody:
        p.vol(row, note, instrument=1, volume=3)
    return p

def harmony_echo_A1():
    """Harmony A1 at whisper volume."""
    p = Pattern()
    melody = [(0, Eb4), (8, G4), (16, C5), (20, Bb4),
              (24, Ab4), (28, G4),
              (32, F4), (36, Ab4), (40, G4),
              (48, Eb4), (52, F4), (56, G4)]
    for row, note in melody:
        p.vol(row, note, instrument=2, volume=2)
    return p

def harmony_echo_A2():
    """Harmony A2 at whisper volume."""
    p = Pattern()
    melody = [(0, Eb5), (8, D5), (16, C5), (20, Bb4),
              (24, Ab4), (28, Bb4),
              (32, C5), (36, Bb4), (40, Ab4),
              (48, G4), (52, Ab4), (56, Bb4)]
    for row, note in melody:
        p.vol(row, note, instrument=2, volume=2)
    return p

def bass_echo_drive():
    """Bass at whisper volume for echo intro."""
    p = Pattern()
    bass = [(0, C3), (4, C4), (8, C3), (12, C4),
            (16, C3), (20, C4), (24, C3), (28, C4),
            (32, Ab3), (36, Ab3), (40, Ab3), (44, Ab3),
            (48, G3), (52, G3), (56, G3), (60, G3)]
    for row, note in bass:
        p.vol(row, note, instrument=1, volume=1)
    return p

def bass_echo_groove():
    """Groovy bass at whisper volume for echo intro."""
    p = Pattern()
    bass = [(0, C3), (4, C3), (6, Eb3), (8, G3),
            (14, C3), (16, C3), (20, C3), (22, Eb3),
            (24, F3), (30, C3),
            (32, Ab3), (36, Ab3), (38, G3), (40, F3),
            (44, Eb3), (48, G3), (52, G3), (54, F3),
            (56, Eb3), (60, D3)]
    for row, note in bass:
        p.vol(row, note, instrument=1, volume=1)
    return p

def drums_echo():
    """Barely audible pulse for echo intro."""
    p = Pattern()
    for row in [0, 32]:
        p.vol(row, KICK, instrument=3, volume=2)
    return p


# ============================================
# Song assembly
# ============================================

def build_song(ghost_mode='arpeggio'):
    """
    Assemble all patterns and write the song.
    
    ghost_mode: 'arpeggio'     - single-channel arpeggio ghostly effects
                'dualchannel'  - split even/odd frames across CH1/CH2
                'none'         - skip ghostly interludes entirely
    
    Song sections:
    0:  Intro 1 - drums build
    1:  Intro 2 - bass enters
    2:  Section A1 - main theme (C minor)
    3:  Section A2 - answer
    4:  Section A3 - variation
    5:  Section A4 - variation 2 + fill
    6:  Ghost interlude 1a
    7:  Ghost interlude 1b (sweep)
    8:  Section B1 - escalation (Eb minor)
    9:  Section B2 - intense
    10: Section B + fill
    11: Ghost interlude 2a
    12: Ghost interlude 2b
    13: Climax 1
    14: Climax 2
    15: Breakdown
    16: Final drop (= climax reprise)
    17: Ghostly outro
    18: Bittersweet A1 (C major with borrowed minor)
    19: Bittersweet A2
    20: Bittersweet A3
    21: Bittersweet darken (back to minor)
    22: Echo intro 1 (quiet whisper of A1 theme)
    23: Echo intro 2 (quiet whisper of A2 theme)
    """
    
    # Select ghost patterns based on mode
    if ghost_mode == 'dualchannel':
        # Dual-channel: split oscillation across CH1 and CH2
        ghost_1a_ch1 = ghostly_dual_A()
        ghost_1a_ch2 = ghostly_dual_B()
        ghost_1b_ch1 = ghostly_dual_A()      # sweep approximation
        ghost_1b_ch2 = ghostly_dual_B()
        ghost_2a_ch1 = ghostly_dual_A()
        ghost_2a_ch2 = ghostly_dual_B()
        ghost_2b_ch1 = ghostly_dual_A()
        ghost_2b_ch2 = ghostly_dual_B()
        outro_ch1    = ghostly_dual_A()
        outro_ch2    = ghostly_dual_B()
    elif ghost_mode == 'none':
        # No ghosts: use silence/empty
        ghost_1a_ch1 = lead_silent()
        ghost_1a_ch2 = harmony_silent()
        ghost_1b_ch1 = lead_silent()
        ghost_1b_ch2 = harmony_silent()
        ghost_2a_ch1 = lead_silent()
        ghost_2a_ch2 = harmony_silent()
        ghost_2b_ch1 = lead_silent()
        ghost_2b_ch2 = harmony_silent()
        outro_ch1    = lead_silent()
        outro_ch2    = harmony_silent()
    else:  # 'arpeggio' (default)
        ghost_1a_ch1 = ghostly_arp_low()
        ghost_1a_ch2 = ghostly_arp_mid()
        ghost_1b_ch1 = ghostly_arp_sweep()
        ghost_1b_ch2 = ghostly_arp_high()
        ghost_2a_ch1 = ghostly_arp_high()
        ghost_2a_ch2 = ghostly_arp_low()
        ghost_2b_ch1 = ghostly_dual_A()
        ghost_2b_ch2 = ghostly_dual_B()
        outro_ch1    = ghostly_arp_sweep()
        outro_ch2    = ghostly_arp_low()
    
    # CH1 (Lead)
    ch1_patterns = [
        lead_silent(),        # 0: intro
        lead_silent(),        # 1: intro 2
        lead_main_A1(),       # 2
        lead_main_A2(),       # 3
        lead_main_A3(),       # 4
        lead_main_A4(),       # 5
        ghost_1a_ch1,         # 6: ghost 1a
        ghost_1b_ch1,         # 7: ghost 1b
        lead_B1(),            # 8
        lead_B2(),            # 9
        lead_main_A3(),       # 10: reuse A3 with fill drums
        ghost_2a_ch1,         # 11: ghost 2a
        ghost_2b_ch1,         # 12: ghost 2b
        lead_climax_1(),      # 13
        lead_climax_2(),      # 14
        lead_silent(),        # 15: breakdown
        lead_climax_1(),      # 16: final drop
        outro_ch1,            # 17: outro
        lead_bittersweet_A1(),      # 18: bittersweet mirror
        lead_bittersweet_A2(),      # 19
        lead_bittersweet_A3(),      # 20
        lead_bittersweet_darken(),  # 21: the turn back to darkness
        lead_echo_A1(),             # 22: echo intro 1
        lead_echo_A2(),             # 23: echo intro 2
    ]
    
    # CH2 (Harmony)
    ch2_patterns = [
        harmony_silent(),       # 0
        harmony_silent(),       # 1
        harmony_A1(),           # 2
        harmony_A2(),           # 3
        harmony_A1(),           # 4
        harmony_A2(),           # 5
        ghost_1a_ch2,           # 6: ghost complement
        ghost_1b_ch2,           # 7
        harmony_B1(),           # 8
        harmony_B1(),           # 9
        harmony_A2(),           # 10
        ghost_2a_ch2,           # 11
        ghost_2b_ch2,           # 12
        harmony_climax(),       # 13
        harmony_climax(),       # 14
        harmony_breakdown(),    # 15
        harmony_climax(),       # 16
        outro_ch2,              # 17
        harmony_bittersweet_A1(),     # 18: bittersweet mirror
        harmony_bittersweet_A2(),     # 19
        harmony_bittersweet_A1(),     # 20
        harmony_bittersweet_darken(), # 21: the turn
        harmony_echo_A1(),             # 22: echo intro 1
        harmony_echo_A2(),             # 23: echo intro 2
    ]
    
    # CH3 (Bass - Wave)
    ch3_patterns = [
        empty_pattern(),        # 0: intro
        bass_cminor_drive(),    # 1
        bass_cminor_drive(),    # 2
        bass_cminor_groove(),   # 3
        bass_cminor_groove(),   # 4
        bass_cminor_drive(),    # 5
        bass_ghost_hold(),      # 6
        bass_ghost_hold(),      # 7
        bass_ebminor_drive(),   # 8
        bass_ebminor_drive(),   # 9
        bass_cminor_drive(),    # 10
        bass_ghost_hold(),      # 11
        bass_ghost_hold(),      # 12
        bass_climax(),          # 13
        bass_climax(),          # 14
        bass_breakdown(),       # 15
        bass_climax(),          # 16
        bass_ghost_hold(),      # 17
        bass_bittersweet_drive(),    # 18: bittersweet mirror
        bass_bittersweet_groove(),   # 19
        bass_bittersweet_groove(),   # 20
        bass_darken(),               # 21: the turn
        bass_echo_drive(),           # 22: echo intro 1
        bass_echo_groove(),          # 23: echo intro 2
    ]
    
    # CH4 (Drums - Noise)
    ch4_patterns = [
        drums_buildup_1(),    # 0
        drums_buildup_2(),    # 1
        drums_main(),         # 2
        drums_main(),         # 3
        drums_intense(),      # 4
        drums_fill(),         # 5
        drums_sparse_ghost(), # 6
        drums_sparse_ghost(), # 7
        drums_intense(),      # 8
        drums_intense(),      # 9
        drums_fill(),         # 10
        drums_sparse_ghost(), # 11
        drums_sparse_ghost(), # 12
        drums_climax(),       # 13
        drums_climax(),       # 14
        drums_halftime(),     # 15
        drums_climax(),       # 16
        drums_sparse_ghost(), # 17
        drums_bittersweet(),       # 18: bittersweet mirror
        drums_bittersweet(),       # 19
        drums_bittersweet(),       # 20
        drums_darken_fill(),       # 21: the turn
        drums_echo(),              # 22: echo intro 1
        drums_echo(),              # 23: echo intro 2
    ]
    
    # Song order: the emotional journey
    if ghost_mode == 'none':
        # No ghostly interludes -- straight through, tighter structure
        song_order = [
            # === ECHO INTRO: ghostly whisper of main theme ===
            22, 23,
            
            # === ACT 1: Establishment (full blast) ===
            2, 3, 4, 5,
            2, 3, 4, 5,
            
            # === ACT 2: Escalation ===
            8, 9, 8, 10,
            
            # === ACT 3: Peak Intensity ===
            8, 9, 10,
            13, 14, 13, 14,
            
            # === ACT 4: Bittersweet Relief ===
            15, 15,
            18, 19, 20,
            
            # === ACT 5: The Turn ===
            21,
            2, 3, 4, 5,
            
            # === ACT 6: Final Reckoning ===
            16, 14, 16, 14,
        ]
    else:
        song_order = [
            # === ECHO INTRO: ghostly whisper of main theme ===
            22, 23,
            
            # === ACT 1: Establishment (full blast) ===
            2, 3, 4, 5,
            2, 3, 4, 5,
            
            # === ACT 2: The Haunting ===
            6, 7, 6,
            8, 9, 8, 10,
            11, 12,
            
            # === ACT 3: Peak Intensity ===
            8, 9, 10,
            13, 14, 13, 14,
            
            # === ACT 4: Bittersweet Relief ===
            15, 15,
            18, 19, 20,
            
            # === ACT 5: The Turn ===
            21,
            2, 3, 4, 5,
            
            # === ACT 6: Final Reckoning ===
            16, 14, 16, 14,
            17, 17, 17,
        ]
    
    return ch1_patterns, ch2_patterns, ch3_patterns, ch4_patterns, song_order


def write_song(output_path, ghost_mode='arpeggio'):
    ch1_pats, ch2_pats, ch3_pats, ch4_pats, song_order = build_song(ghost_mode)
    
    n = len(ch1_pats)  # patterns per channel
    # Pattern key layout: CH1: 0..n-1, CH2: n..2n-1, CH3: 2n..3n-1, CH4: 3n..4n-1, empty: 4n
    empty_key = 4 * n
    total_keys = 4 * n + 1
    
    with open(output_path, 'wb') as f:
        # Header
        write_uge_int(f, UGE_FORMAT_VERSION)
        write_uge_shortstring(f, "Phantom Dash")
        write_uge_shortstring(f, "")
        write_uge_shortstring(f, "A ghastly rhythm game track")
        
        # ---- INSTRUMENTS ----
        # 15 Duty instruments (for CH1, CH2)
        # 0: Lead (25% duty = sharp, piercing)
        write_uge_instrument(f, type_=0, name="Lead Sharp",
                           initial_volume=12, duty=1,
                           vol_sweep_dir=1, vol_sweep_amount=2)  # slight decay
        # 1: Harmony (50% duty = rounder)
        write_uge_instrument(f, type_=0, name="Harmony",
                           initial_volume=10, duty=2)
        # 2: Ghost Tone (50% duty, sustained)
        write_uge_instrument(f, type_=0, name="Ghost",
                           initial_volume=8, duty=2)
        # 3-14: empty
        for _ in range(12):
            write_uge_instrument(f, type_=0)
        
        # 15 Wave instruments (for CH3)
        # 0: Bass (triangle-ish, full volume)
        write_uge_instrument(f, type_=1, name="Bass", output_level=1)
        for _ in range(14):
            write_uge_instrument(f, type_=1)
        
        # 15 Noise instruments (for CH4)
        # 0: Hi-hat (short, quiet)
        write_uge_instrument(f, type_=2, name="HiHat",
                           initial_volume=6, length=8, length_enabled=True,
                           vol_sweep_dir=1, vol_sweep_amount=3)
        # 1: Snare (medium)
        write_uge_instrument(f, type_=2, name="Snare",
                           initial_volume=12, length=16, length_enabled=True,
                           vol_sweep_dir=1, vol_sweep_amount=2)
        # 2: Kick (long, powerful)
        write_uge_instrument(f, type_=2, name="Kick",
                           initial_volume=15, length=24, length_enabled=True,
                           vol_sweep_dir=1, vol_sweep_amount=1)
        for _ in range(12):
            write_uge_instrument(f, type_=2)
        
        # ---- WAVES ----
        # Wave 0: Triangle (good for bass)
        triangle = list(range(16)) + list(range(15, -1, -1))
        f.write(bytes(triangle))
        # Wave 1: Sawtooth
        f.write(bytes([i % 16 for i in range(32)]))
        # Wave 2: Pulse 50%
        f.write(bytes([0]*16 + [15]*16))
        # Wave 3: Soft sine approximation
        sine_approx = [8,10,12,13,14,15,15,15,14,13,12,10,8,6,4,3,2,1,1,1,2,3,4,6,8,8,8,8,8,8,8,8]
        f.write(bytes(sine_approx))
        # Waves 4-15: zeroed
        for _ in range(12):
            f.write(bytes(32))
        
        # ---- TIMING ----
        write_uge_int(f, 3)     # ticks_per_row = 3
        f.write(bytes([0]))     # timer disabled
        write_uge_int(f, 0)     # timer divider
        
        # ---- PATTERNS ----
        write_uge_int(f, total_keys)
        
        # Write CH1 patterns
        for i, pat in enumerate(ch1_pats):
            pat.write(f, i)
        
        # Write CH2 patterns
        for i, pat in enumerate(ch2_pats):
            pat.write(f, n + i)
        
        # Write CH3 patterns
        for i, pat in enumerate(ch3_pats):
            pat.write(f, 2*n + i)
        
        # Write CH4 patterns
        for i, pat in enumerate(ch4_pats):
            pat.write(f, 3*n + i)
        
        # Empty pattern
        write_uge_int(f, empty_key)
        for _ in range(64):
            write_uge_cell(f)
        
        # ---- ORDER MATRIX ----
        order_len = len(song_order) + 1  # +1 for loop-back
        
        # CH1 order
        write_uge_int(f, order_len)
        for idx in song_order:
            write_uge_int(f, idx)         # CH1 pattern keys: 0..n-1
        write_uge_int(f, 0)  # loop to start
        
        # CH2 order
        write_uge_int(f, order_len)
        for idx in song_order:
            write_uge_int(f, n + idx)     # CH2 pattern keys: n..2n-1
        write_uge_int(f, 0)
        
        # CH3 order
        write_uge_int(f, order_len)
        for idx in song_order:
            write_uge_int(f, 2*n + idx)   # CH3 pattern keys: 2n..3n-1
        write_uge_int(f, 0)
        
        # CH4 order
        write_uge_int(f, order_len)
        for idx in song_order:
            write_uge_int(f, 3*n + idx)   # CH4 pattern keys: 3n..4n-1
        write_uge_int(f, 0)
        
        # ---- ROUTINES ----
        for _ in range(16):
            write_uge_int(f, 0)
    
    import os
    file_size = os.path.getsize(output_path)
    
    # Calculate duration
    total_rows = len(song_order) * 64
    seconds = total_rows * 3 / 59.7  # ticks_per_row * rows / ticks_per_sec
    
    print(f"Song: Phantom Dash")
    print(f"Key: C minor, ~149 BPM")
    print(f"Ghost mode: {ghost_mode}")
    print(f"Patterns: {n} per channel x 4 channels + 1 empty = {total_keys}")
    print(f"Song order: {len(song_order)} entries")
    print(f"Duration: ~{seconds:.0f} seconds ({seconds/60:.1f} minutes)")
    print(f"Output: {output_path} ({file_size} bytes)")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate Phantom Dash .uge song')
    parser.add_argument('output', nargs='?', default='phantom_dash.uge',
                        help='Output .uge file path')
    parser.add_argument('-g', '--ghost', choices=['arpeggio', 'dualchannel', 'none'],
                        default='arpeggio',
                        help='Ghost interlude mode (default: arpeggio)')
    args = parser.parse_args()
    write_song(args.output, ghost_mode=args.ghost)
