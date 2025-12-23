INCLUDE "hardware.inc"


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
    ;ld de, Tilemap
    ;ld hl, $9800
    ;ld bc, TilemapEnd - Tilemap
		;call Memcopy
    ld b ,0
    ld de, 0
    ld hl, 0
    ld c ,$20
    startuptilecopy:
    dec c
    ld e, c
    ld l, c
    call CopyColumn
    jp nz, startuptilecopy

    ; Copy the paddle tile
    ld de, MainLeft
    ld hl, $8000
    ld bc, MainRightEnd - MainLeft
		call Memcopy

    ld a, 0
    ld b, 160
    ld hl, _OAMRAM
ClearOam:
    ld [hli], a
    dec b
    jp nz, ClearOam

		; Initialize the main left sprite in OAM
    ld hl, _OAMRAM
    ld a, 0 + 16
    ld [hli], a
    ld a, 0 + 8
    ld [hli], a
    ld a, 0
    ld [hli], a
    ld [hli], a
    ; Now initialize the main right sprite
    ld a, 0 + 16
    ld [hli], a
    ld a, 0 + 8
    ld [hli], a
    ld a, 2
    ld [hli], a
    ld a, 0
    ld [hli], a

    ; The ball starts out going up and to the right
    ld a, 1 ; 1 pixel per frame scrolling
    ld [wScrollSpeedLow], a
    ld a, 0
    ld [wScrollSpeedLow+1], a
    ld [wScrollSpeedHigh], a
    ld [wScrollSpeedHigh+1], a
    ld [wScrollCounterLow], a
    ld [wScrollCounterLow+1], a
    ld [wScrollCounterHigh], a
    ld [wScrollCounterHigh+1], a
    ld [wMainMomentumX], a
    ld [wMainMomentumY], a
    ld [wMainMomentumX+1], a
    ld [wMainMomentumY+1], a
    ld [wMainX], a
    ld [wMainY], a
    ld a,20
    ld [wMainX+1], a
    ld a,20
    ld [wMainY+1], a


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
    ld hl, wScrollCounterLow
    ld de, wScrollSpeedLow
    call Add32
    ld a, [wScrollCounterLow] ; TODO: prepare the tile map beyond 256
    ld [rSCX] ,a
    
    call ScrollLevel
    

    ; Load wMainY into hl (destroying a)
    ld a, [wMainY]
    ld l, a
    ld a, [wMainY+1] 
    ld h, a 

    ; Put wMainMomentumY is in de.
    ld a, [wMainMomentumY]
    ld e, a
    ld a, [wMainMomentumY+1] 
    ld d, a 
    ; Do a 16 bit add 
    add hl, de

    ; put hl into wMainY
    ld a, l
    ld [wMainY], a
    ld a, h
    ld [wMainY + 1], a
    call PlayerMovement


    ; Update the OAM
    ld a, [wMainY+1]
    add a, 16
    ld [_OAMRAM + 0],a
    ld [_OAMRAM + 4],a

    ld a, [wMainX+1]
    add a, 8
    ld [_OAMRAM + 1],a
    add a, 8
    ld [_OAMRAM + 5],a

    ; Add the ball's momentum to its position in OAM.
    
    ; First, check if the left button is pressed.
    call UpdateKeys

    
    
; Then check the right button.

    jp Main



PlayerMovement:
  call Turn
  call Gravity
  ; check if touching the ground
  call CheckFloorTile
  ; if not touching ground, go to .DoneTouchingGround
  jp nz ,.DoneTouchingGround
    ; if Speed < 0 (bit 7 wMainMomentumY + 1) go to BonkedCeiling
    ld a ,[wMainMomentumY+1]
    bit 7,a 
    jp nz ,.BonkedCeiling
    ; Move Out Of Level with dy = -1 -> hl
    ld h, $ff
    ld l, $00
    call MoveOutofLevel
  call CheckUp ; only do the jump key when in the ground.

  .DoneTouchingGround:
  ret
  .BonkedCeiling:
    call GameOver
  ret
  

INCLUDE "func.asm"

INCLUDE "util.asm"

INCLUDE "tiles.asm"

INCLUDE "sprites.asm"

INCLUDE "startlevel.asm"

INCLUDE "level.asm"




INCLUDE "var.asm"
