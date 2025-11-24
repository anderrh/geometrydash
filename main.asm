INCLUDE "hardware.inc"

DEF BRICK_LEFT EQU $05
DEF BRICK_RIGHT EQU $06
DEF DIGIT_OFFSET EQU $1A
DEF BLANK_TILE EQU $08
DEF SCORE_TENS   EQU $9870
DEF SCORE_ONES   EQU $9871

SECTION "header", ROM0[$100]

    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:
    ; Do not turn the LCD off outside of VBlank
WaitVBlank:
    ld a, [rLY]
    cp 144
    jp c, WaitVBlank

    ; Turn the LCD off
    ld a, 0
    ld [rLCDC], a

    ; Copy the tile data
    ld de, Tiles
    ld hl, $9000
    ld bc, TilesEnd - Tiles
		call Memcopy

    ; Copy the tilemap
    ld de, Tilemap
    ld hl, $9800
    ld bc, TilemapEnd - Tilemap
		call Memcopy

    ; Copy the paddle tile
    ld de, MainLeft
    ld hl, $8000
    ld bc, MainLeftEnd - MainLeft
		call Memcopy

		; Copy the ball tile
		ld de, MainRight
    ld hl, $8020
    ld bc, BallEnd - MainRight
    call Memcopy

    ld a, 0
    ld b, 160
    ld hl, _OAMRAM
ClearOam:
    ld [hli], a
    dec b
    jp nz, ClearOam
    ;ld a, LCDCF_ON | LCDCF_OBJON | LCDCF_OBJ16 | LCDCF_BGON ;we added this monday
    ;ld [rLCDC], a


		; Initialize the paddle sprite in OAM
    ld hl, _OAMRAM
    ld a, 128 + 16
    ld [hli], a
    ld a, 16 + 8
    ld [hli], a
    ld a, 0
    ld [hli], a
    ld [hli], a
    ; Now initialize the ball sprite
    ld a, 100 + 16
    ld [hli], a
    ld a, 32 + 8
    ld [hli], a
    ld a, 2
    ld [hli], a
    ld a, 0
    ld [hli], a

    ; The ball starts out going up and to the right
    ld a, 1
    ld [wBallMomentumX], a
    ld a, -1
    ld [wBallMomentumY], a

    ; Turn the LCD on
    ld a, LCDCF_ON | LCDCF_BGON | LCDCF_OBJON | LCDCF_OBJ16 ; danielrh added
    ld [rLCDC], a

    ; During the first (blank) frame, initialize display registers
    ld a, %11100100
    ld [rBGP], a
    ld a, %11100100
    ld [rOBP0], a

    ; Initialize global variables
    ld a, 0
    ld [wFrameCounter], a
    ld [wCurKeys], a
    ld [wNewKeys], a
    ld [wScore], a

Main:
    ld a, [rLY]
    cp 144
    jp nc, Main
WaitVBlank2:
    ld a, [rLY]
    cp 144
    jp c, WaitVBlank2
    ld a, [wFrameCounter]
    inc a
    ld [wFrameCounter], a
    add a, a
    ld [rSCX] ,a
    ; Add the ball's momentum to its position in OAM.
    ld a, [wBallMomentumX]
    ld b, a
    ld a, [_OAMRAM + 5]
    add a, b
    ld [_OAMRAM + 5], a

    ld a, [wBallMomentumY]
    ld b, a
    ld a, [_OAMRAM + 4]
    add a, b
    ld [_OAMRAM + 4], a

		BounceOnTop:
    ; Remember to offset the OAM position!
    ; (8, 16) in OAM coordinates is (0, 0) on the screen.
    ld a, [_OAMRAM + 4]
    sub a, 16 + 1
    ld c, a
    ld a, [_OAMRAM + 5]
    sub a, 8
    ld b, a
    call GetTileByPixel ; Returns tile address in hl
    ld a, [hl]
    call IsWallTile
    jp nz, BounceOnRight
		call CheckAndHandleBrick
    ld a, 1
    ld [wBallMomentumY], a

BounceOnRight:
    ld a, [_OAMRAM + 4]
    sub a, 16
    ld c, a
    ld a, [_OAMRAM + 5]
    sub a, 8 - 1
    ld b, a
    call GetTileByPixel
    ld a, [hl]
    call IsWallTile
    jp nz, BounceOnLeft
		call CheckAndHandleBrick
    ld a, -1
    ld [wBallMomentumX], a

BounceOnLeft:
    ld a, [_OAMRAM + 4]
    sub a, 16
    ld c, a
    ld a, [_OAMRAM + 5]
    sub a, 8 + 1
    ld b, a
    call GetTileByPixel
    ld a, [hl]
    call IsWallTile
    jp nz, BounceOnBottom
		call CheckAndHandleBrick
    ld a, 1
    ld [wBallMomentumX], a

BounceOnBottom:
    ld a, [_OAMRAM + 4]
    sub a, 16 - 1
    ld c, a
    ld a, [_OAMRAM + 5]
    sub a, 8
    ld b, a
    call GetTileByPixel
    ld a, [hl]
    call IsWallTile
    jp nz, BounceDone
		call CheckAndHandleBrick
    ld a, -1
    ld [wBallMomentumY], a
BounceDone:
    ; First, check if the ball is low enough to bounce off the paddle.
    ld a, [_OAMRAM]
    ld b, a
    ld a, [_OAMRAM + 4]
    add a, $4
    cp a, b
    jp nz, MainLeftBounceDone ; If the ball isn't at the same Y position as the paddle, it can't bounce.
    ; Now let's compare the X positions of the objects to see if they're touching.
    ld a, [_OAMRAM + 5] ; MainRight's X position.
    ld b, a
    ld a, [_OAMRAM + 1] ; MainLeft's X position.
    sub a, 8
    cp a, b
    jp nc, MainLeftBounceDone
    add a, 8 + 16 ; 8 to undo, 16 as the width.
    cp a, b
    jp c, MainLeftBounceDone

    ld a, -1
    ld [wBallMomentumY], a

MainLeftBounceDone:
    ; Check the current keys every frame and move left or right.
    call UpdateKeys

    ; First, check if the left button is pressed.
CheckUp:
    ld a, [wCurKeys]
    and a, PADF_UP
    jp z, CheckDown
Up:
    ; Move the paddle one pixel to the left.
    ld a, [_OAMRAM + 0]
    dec a
    ; If we've already hit the edge of the playfield, don't move.
    cp a, 15
    jp z, Main
    ld [_OAMRAM + 0], a
    jp Main

; Then check the right button.
CheckDown:
    ld a, [wCurKeys]
    and a, PADF_DOWN
    jp z, Main
Down:
    ; Move the paddle one pixel to the right.
    ld a, [_OAMRAM + 0]
    inc a
    ; If we've already hit the edge of the playfield, don't move.
    cp a, 105
    jp z, Main
    ld [_OAMRAM + 0], a
    jp Main

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
    ld a, b
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

; @param a: tile ID
; @return z: set if a is a wall.
IsWallTile:
    cp a, $00
    ret z
    cp a, $01
    ret z
    cp a, $02
    ret z
    cp a, $04
    ret z
    cp a, $05
    ret z
    cp a, $06
    ret z
    cp a, $07
    ret
		
; Checks if a brick was collided with and breaks it if possible.
; @param hl: address of tile.
CheckAndHandleBrick:
    ld a, [hl]
    cp a, BRICK_LEFT
    jr nz, CheckAndHandleBrickRight
    ; Break a brick from the left side.
    ld [hl], BLANK_TILE
    inc hl
    ld [hl], BLANK_TILE
		call IncreaseScorePackedBCD
CheckAndHandleBrickRight:
    cp a, BRICK_RIGHT
    ret nz
    ; Break a brick from the right side.
    ld [hl], BLANK_TILE
    dec hl
    ld [hl], BLANK_TILE
		call IncreaseScorePackedBCD
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
Tiles:
  dw `00000000
	dw `00000000
	dw `00000000
	dw `00000000
	dw `00000000
	dw `00000000
	dw `00000000
	dw `00000000

	dw `33333333
	dw `31111113
	dw `31333313
	dw `31322313
	dw `31322313
	dw `31333313
	dw `31111113
	dw `33333333

	dw `00033000
	dw `00033000
	dw `00312300
	dw `00312300
	dw `03112230
	dw `03112230
	dw `31112223
	dw `33333333

	dw `00033000
	dw `00033000
	dw `00033000
	dw `00033000
	dw `00312300
	dw `00312300
	dw `00312300
	dw `00312300
	dw `03112230
	dw `03112230
	dw `03112230
	dw `03112230
	dw `31112223
	dw `31112223
	dw `31112223
	dw `31112223

	dw `00000000
	dw `00000000
	dw `00000000
	dw `00000000
	dw `00030000
	dw `03033030
	dw `32322333
	dw `21211212

	dw `00000000
	dw `00000000
	dw `00000000
	dw `00000000
	dw `00333300
	dw `03111130
	dw `32222223
	dw `33333333

	dw `33333333
	dw `32222223
	dw `03111130
	dw `00333300
	dw `00000000
	dw `00000000
	dw `00000000
	dw `00000000

  dw `00000000
	dw `00333300
	dw `03111130
	dw `03122130
	dw `03122130
	dw `03111130
	dw `00333300
	dw `00000000

	dw `03333330
	dw `33222233
	dw `32200223
	dw `32000023
	dw `32000023
	dw `32200223
	dw `33222233
	dw `03333330

	dw `00333300
	dw `00300300
	dw `00300300
	dw `00300300
	dw `00300300
	dw `00300300
	dw `00300300
	dw `00333300

	dw `00000000
	dw `00000000
	dw `33333333
	dw `30000003
	dw `30000003
	dw `33333333
	dw `00000000
	dw `00000000

	dw `33000000
	dw `33300000
	dw `31330000
	dw `31133000
	dw `31133000
	dw `31330000
	dw `33300000
	dw `33000000

	dw `00000033
	dw `00000333
	dw `00003313
	dw `00033113
	dw `00033113
	dw `00003313
	dw `00000333
	dw `00000033

	dw `33333333
	dw `33111133
	dw `03311330
	dw `00333300
	dw `00033000
	dw `00000000
	dw `00000000
	dw `00000000

	dw `00000000
	dw `00000000
	dw `00000000
	dw `00033000
	dw `00333300
	dw `03300330
	dw `33000033
	dw `33333333

	dw `02022202
	dw `02020202
	dw `22022202
	dw `02020202
	dw `00000000
	dw `20220022
	dw `20202020
	dw `20202022

	dw `22000010
	dw `02000020
	dw `20000020
	dw `02000020
	dw `00000020
	dw `20222020
	dw `00202030
	dw `00220030

	dw `03022200
	dw `03000000
	dw `03300000
	dw `00330000
	dw `00033300
	dw `00003333
	dw `00000033
	dw `00000033

	dw `02020200
	dw `00000000
	dw `00000000
	dw `00000000
	dw `00000000
	dw `33333333
	dw `33000003
	dw `30000003

	dw `20220022
	dw `00000000
	dw `00000000
	dw `00000000
	dw `00000000
	dw `33333333
	dw `30000033
	dw `30000003

	dw `20202030
	dw `00000030
	dw `00000330
	dw `00003300
	dw `00333000
	dw `33330000
	dw `33000000
	dw `33000000

	dw `00000333
	dw `00003330
	dw `00003300
	dw `00003300
	dw `00003300
	dw `00333333
	dw `00000000
	dw `00000000

	dw `00000003
	dw `00000003
	dw `00000003
	dw `00000003
	dw `00000003
	dw `00000333
	dw `00000000
	dw `00000000

	dw `30000000
	dw `30000000
	dw `30000000
	dw `30000000
	dw `30000000
	dw `33300000
	dw `00000000
	dw `00000000

	dw `33300000
	dw `03330000
	dw `00330000
	dw `00330000
	dw `00330000
	dw `33333300
	dw `00000000
	dw `00000000

; digits
	; 0
	dw `33333333
	dw `33000033
	dw `30033003
	dw `30033003
	dw `30033003
	dw `30033003
	dw `33000033
	dw `33333333
	; 1
	dw `33333333
	dw `33300333
	dw `33000333
	dw `33300333
	dw `33300333
	dw `33300333
	dw `33000033
	dw `33333333
	; 2
	dw `33333333
	dw `33000033
	dw `30330003
	dw `33330003
	dw `33000333
	dw `30003333
	dw `30000003
	dw `33333333
	; 3
	dw `33333333
	dw `30000033
	dw `33330003
	dw `33000033
	dw `33330003
	dw `33330003
	dw `30000033
	dw `33333333
	; 4
	dw `33333333
  dw `33000033
  dw `30030033
  dw `30330033
  dw `30330033
  dw `30000003
  dw `33330033
  dw `33333333
  ; 5
  dw `33333333
  dw `30000033
  dw `30033333
  dw `30000033
  dw `33330003
  dw `30330003
  dw `33000033
  dw `33333333
  ; 6
  dw `33333333
  dw `33000033
  dw `30033333
  dw `30000033
  dw `30033003
  dw `30033003
  dw `33000033
  dw `33333333
  ; 7
  dw `33333333
  dw `30000003
  dw `33333003
  dw `33330033
  dw `33300333
  dw `33000333
  dw `33000333
  dw `33333333
  ; 8
  dw `33333333
  dw `33000033
  dw `30333003
  dw `33000033
  dw `30333003
  dw `30333003
  dw `33000033
  dw `33333333
  ; 9
  dw `33333333
  dw `33000033
  dw `30330003
  dw `30330003
  dw `33000003
  dw `33330003
  dw `33000033
  dw `33333333
TilesEnd:

Tilemap:
	db $00, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $02, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $05, $06, $05, $06, $05, $06, $05, $06, $05, $06, $05, $06, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $05, $06, $05, $06, $05, $06, $05, $06, $05, $06, $08, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $05, $06, $05, $06, $05, $06, $05, $06, $05, $06, $05, $06, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $05, $06, $05, $06, $05, $06, $05, $06, $05, $06, $08, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $05, $06, $05, $06, $05, $06, $05, $06, $05, $06, $05, $06, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $05, $06, $05, $06, $05, $06, $05, $06, $05, $06, $08, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $07, $03, $03, $03, $03, $03, $03, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $07, $00, $01, $01, $01, $01, $02, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $07, $04, $0A, $0B, $0C, $0D, $07, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $07, $04, $0E, $0F, $10, $11, $07, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $07, $04, $12, $13, $14, $15, $07, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $04, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $08, $07, $04, $16, $17, $18, $19, $07, $07, 0,0,0,0,0,0,0,0,0,0,0
	db $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, $01, 
TilemapEnd:



MainLeft:
    dw `00000000
    dw `00000000
    dw `00000000
    dw `00000000
    dw `00003333
    dw `00003111
    dw `00003133
    dw `00003132
    dw `00003132
    dw `00003133
    dw `00003111
    dw `00003333
    dw `00000000
    dw `00000000
    dw `00000000
    dw `00000000
    
MainLeftEnd:

MainRight:
    dw `00000000
    dw `00000000
    dw `00000000
    dw `00000000
    dw `33330000
    dw `11130000
    dw `33130000
    dw `23130000
    dw `23130000
    dw `33130000
    dw `11130000
    dw `33330000
    dw `00000000
    dw `00000000
    dw `00000000
    dw `00000000
BallEnd:

SECTION "Counter", WRAM0
wFrameCounter: db

SECTION "Input Variables", WRAM0
wCurKeys: db
wNewKeys: db

SECTION "MainRight Data", WRAM0
wBallMomentumX: db
wBallMomentumY: db

SECTION "Score", WRAM0
wScore: db