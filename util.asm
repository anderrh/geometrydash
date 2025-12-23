DEF SCORE_TENS   EQU $9870
DEF SCORE_ONES   EQU $9871
DEF DIGIT_OFFSET   EQU $0


DEF ooo EQU $10
DEF BBB EQU $11
DEF AAA EQU $12
DEF vvv EQU $13
DEF iii EQU $14
DEF III EQU $15
DEF uuu EQU $16


; Copy bytes from one area to another.
; @param de: Source
; @param hl: Destination
; @param bc: Length
Memcopy:
    ld a, [de]
    ld [hli], a
    inc de
    dec bc
    ld a, b
    or a, c
    jp nz, Memcopy
    ret

UpdateKeys:
  ; Poll half the controller
  ld a, P1F_GET_BTN
  call .onenibble
  ld b, a ; B7-4 = 1; B3-0 = unpressed buttons

  ; Poll the other half
  ld a, P1F_GET_DPAD
  call .onenibble
  swap a ; A7-4 = unpressed directions; A3-0 = 1
  xor a, b ; A = pressed buttons + directions
  ld b, a ; B = pressed buttons + directions

  ; And release the controller
  ld a, P1F_GET_NONE
  ldh [rP1], a

  ; Combine with previous wCurKeys to make wNewKeys
  ld a, [wCurKeys]
  xor a, b ; A = keys that changed state
  and a, b ; A = keys that changed to pressed
  ld [wNewKeys], a
  ld a, b
  ld [wCurKeys], a
  ret

.onenibble
  ldh [rP1], a ; switch the key matrix
  call .knownret ; burn 10 cycles calling a known ret
  ldh a, [rP1] ; ignore value while waiting for the key matrix to settle
  ldh a, [rP1]
  ldh a, [rP1] ; this read counts
  or a, $F0 ; A7-4 = 1; A3-0 = unpressed keys
.knownret
  ret

; Convert a pixel position to a tilemap address
; hl = $9800 + X + Y * 32
; @param b: X
; @param c: Y
; @return hl: tile address
GetTileByPixel:
    ; First, we need to divide by 8 to convert a pixel position to a tile position.
    ; After this we want to multiply the Y position by 32.
    ; These operations effectively cancel out so we only need to mask the Y value.
    ld a, c
    and a, %11111000
    ld l, a
    ld h, 0
    ; Now we have the position * 8 in hl
    add hl, hl ; position * 16
    add hl, hl ; position * 32
    ; Convert the X position to an offset.
    ld a, [rSCX]
    add a, b
    srl a ; a / 2
    srl a ; a / 4
    srl a ; a / 8
    ; Add the two offsets together.
    add a, l
    ld l, a
    adc a, h
    sub a, l
    ld h, a
    ; Add the offset to the tilemap's base address, and we are done!
    ld bc, $9800
    add hl, bc
    ret

; Increase score by 1 and store it as a 1 byte packed BCD number
; changes A and HL
IncreaseScorePackedBCD:
    xor a               ; clear carry flag and a
    inc a               ; a = 1
    ld hl, wScore       ; load score
    adc [hl]            ; add 1
    daa                 ; convert to BCD
    ld [hl], a          ; store score
    call UpdateScoreBoard
    ret
		; Read the packed BCD score from wScore and updates the score display
UpdateScoreBoard:
    ld a, [wScore]      ; Get the Packed score
    and %11110000       ; Mask the lower nibble
    swap a              ; Move the upper nibble to the lower nibble (divide by 16)
    add a, DIGIT_OFFSET ; Offset + add to get the digit tile
    ld [SCORE_TENS], a  ; Show the digit on screen

    ld a, [wScore]      ; Get the packed score again
    and %00001111       ; Mask the upper nibble
    add a, DIGIT_OFFSET ; Offset + add to get the digit tile again
    ld [SCORE_ONES], a  ; Show the digit on screen
    ret

  Abs16:
    ; HL = |HL|
    push af
    bit 7,h ; if positive set the flags
    jp z, .AbsReturn
    ld a,h
    cpl
    ld h,a
    ld a,l
    cpl
    ld l,a
    inc hl    
    .AbsReturn:
    pop af
    ret
  Neg16:
    ; hl = -hl
    push af
    
    ld a,h
    cpl
    ld h,a
    ld a,l
    cpl
    ld l,a
    inc hl    
    
    pop af
    ret
  
  Sub16:
      ; Function wants 2 values at HL and DE
    ; HL = HL + DE
    push de
    push af
    ld a,d
    cpl
    ld d,a
    ld a,e
    cpl
    ld e,a
    add hl,de
    inc hl
    pop af
    pop de
    ret

  Add32:
    ; Function wants 2 pointers at HL and DE
    ; [HL] = [HL] + [DE]
    push hl
    push de
    push af

    ld a, [de]
    add a, [hl]
    ld [hli],a
    inc de

    ld a, [de]
    adc a, [hl]
    ld [hli],a
    inc de

    ld a, [de]
    adc a, [hl]
    ld [hli],a
    inc de

    ld a, [de]
    adc a, [hl]
    ld [hl],a
    


    pop af
    pop de
    pop hl
    ret