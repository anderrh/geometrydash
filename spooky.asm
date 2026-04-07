SECTION "Spooky Data", WRAM0
wNoteTable:: ds 144   ; 72 entries x 2 bytes, WRAM copy of note table
wNoteCorruptCount: db  ; how many note entries we've corrupted so far
wWaveCorruptCount: db  ; how many wave RAM bytes we've corrupted so far

SECTION "Spooky Code", ROM0

; Copy ROM note table to WRAM and reset corruption counters.
; Call at level init (whenever wScary is zeroed).
InitNoteTable::
    ld hl, note_table_rom
    ld de, wNoteTable
    ld b, 144
.copy:
    ld a, [hl+]
    ld [de], a
    inc de
    dec b
    jr nz, .copy
    xor a
    ld [wNoteCorruptCount], a
    ld [wWaveCorruptCount], a
    ret

; Approach 2: Corrupt note table entries as wScary rises.
; Target corruptions = wScary / 4 (0-63 at max, covering most of 72 entries).
; Call once per frame after hUGE_dosound.
CorruptNoteEntry::
    ld a, [wScary]
    srl a
    srl a              ; target = wScary >> 2
    ld b, a
    ld a, [wNoteCorruptCount]
    cp b
    ret nc             ; already at or past target
    inc a
    ld [wNoteCorruptCount], a

    ; pick random note index 0-71
.pickNote:
    call GetRandom
    and 127            ; 0-127
    cp 72
    jr nc, .pickNote   ; retry if out of range

    add a              ; x2 for word offset
    ld c, a
    ld b, 0
    ld hl, wNoteTable
    add hl, bc

    ; corrupt: XOR small random value into low byte of frequency
    push hl
    call GetRandom
    pop hl
    and $0F            ; magnitude 0-15
    xor [hl]
    ld [hl], a
    ret

; Approach 3: Corrupt wave RAM as wScary rises.
; Target corruptions = wScary / 16 (0-15, covering all 16 wave bytes at max).
; Call once per frame after hUGE_dosound.
CorruptWaveRAM::
    ld a, [wScary]
    swap a
    and $0F            ; target = wScary >> 4
    ld b, a
    ld a, [wWaveCorruptCount]
    cp b
    ret nc             ; already at or past target
    inc a
    ld [wWaveCorruptCount], a

    ; pick random wave RAM byte 0-15
    call GetRandom
    and $0F
    ld c, a
    ld b, 0
    ld hl, _AUD3WAVERAM
    add hl, bc

    ; disable CH3 before writing wave RAM
    xor a
    ldh [rAUD3ENA], a

    ; write random byte
    push hl
    call GetRandom
    pop hl
    ld [hl], a

    ; re-enable CH3
    ld a, $80
    ldh [rAUD3ENA], a
    ret
