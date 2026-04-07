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

    ; compute target entry pointer and push it
    ld d, a            ; D = target note index (0-71)
    add a              ; x2 for word offset
    ld c, a
    ld b, 0
    ld hl, wNoteTable
    add hl, bc
    push hl            ; save target entry address

    ; pick offset: random 0-7, 0-2 = up 1-3, 3-7 = down 1-5
    call GetRandom
    and $07            ; 0-7
    cp 3
    jr nc, .goDown
    ; go up 1-3: offset = A + 1
    inc a
    ld b, a
    ld a, d
    add a, b
    cp 72
    jr c, .srcOk
    ld a, 71           ; clamp to max
    jr .srcOk
.goDown:
    ; go down 1-5: offset = A - 2 (3->1, 4->2, 5->3, 6->4, 7->5)
    sub 2
    ld b, a
    ld a, d
    sub b
    jr nc, .srcOk
    xor a              ; clamp to 0
.srcOk:
    ; A = source note index, look up its frequency
    add a              ; x2 for word offset
    ld c, a
    ld b, 0
    ld hl, wNoteTable
    add hl, bc
    ld a, [hl+]
    ld d, a            ; D = source low byte
    ld e, [hl]         ; E = source high byte
    pop hl             ; HL = destination entry
    ld [hl], d         ; write low byte
    inc hl
    ld [hl], e         ; write high byte
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
