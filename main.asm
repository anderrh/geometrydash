INCLUDE "include/hardware.inc"

SECTION "header", ROM0[$100]

    jp EntryPoint

    ds $150 - @, 0 ; Make room for the header

EntryPoint:

StartMenu:
     ; setup the menu tilemaps

call WaitVBlank4

    ; initialize menu music
    ld a, 0
    ld [wLevel], a

    ; Stop level sounds.
    ldh [rAUD1ENV], a
    ldh [rAUD2ENV], a
    ldh [rAUD4ENV], a
    ldh [rAUD3ENA], a

    call SetSongBank
    ld hl, menusong
    call hUGE_init
    call InitNoteTable

Menu:
     ld a, [rLY]
     cp 144
     jp nc, Menu
 WaitVBlank3:
     ld a, [rLY]
     cp 144
     jp c, WaitVBlank3

    call SetSongBank
    call hUGE_dosound

    call UpdateKeys


    ld a, [wCurKeys]
    and a, PADF_START
    jp z, .noStart
    ld a, [wCurKeys]
    and a, PADF_LEFT
    ld [wNoSpike], a
    call PlayGame
    .noStart:
    
    ld a, [wCurKeys]
    and a, PADF_UP
    jp z, gamec
    ld a, 2
    ld [wLastKeyDown] ,a
    jp somekeydown
    gamec:
    ld a, [wCurKeys]
    and a, PADF_DOWN
    jp z, gamed
    ld a, 1
    ld [wLastKeyDown] ,a
    jp somekeydown
    gamed:

    ld a,[wLastKeyDown]
    cp a, 0
    jp z, somekeydown
    add a, a
    sub a, 3
    ld b,a
    
    ld a, [wLevelSelector]
    add a,b
    cp a, 1 ; make sure level is a natural number
    jp nc, positive_level
    ld a, 1; if it is a negative level, keep it positive
    positive_level:
    ld [wLevelSelector], a

    add a, a
    add a, a
    add a, a
    ld b, a
    ld a, 88
    sub a, b
    ld b,a
    ld [_OAMRAM], a
    add a,16
    ld [_OAMRAM+4], a
    add a,16
    ld [_OAMRAM+8], a
    add a,16
    ld [_OAMRAM+12], a


    ld a,0
    ld [wLastKeyDown],a


    somekeydown:
    jp Menu
    

PlayGame:
  ld a,[wLevelSelector]
  ld [wLevel],a
  call WaitVBlank
  WaitVBlank4:
  ;finished playing game
  ld a, [rLY]
  cp 144
  jp c, WaitVBlank4

  ;;;setup menu
    ld a, 0
    ld [rLCDC], a
    ld [wLevel], a
    ld [rSCX],a

    call SetLevelBank
    ; Copy the tile data
    ld de, MenuTiles
    ld hl, $9000
    ld bc, MenuTilesEnd - MenuTiles
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
    startuptilecopy2:
    dec c
    ld e, c
    ld l, c
    call CopyColumn
    jp nz, startuptilecopy2

    ; Copy the paddle tile
    ld de, MenuNumberSprites
    ld hl, $8000
    ld bc, MenuNumberSpritesEnd - MenuNumberSprites
		call Memcopy

    ld a, 0
    ld b, 160
    ld hl, _OAMRAM
ClearOam2:
    ld [hli], a
    dec b
    jp nz, ClearOam2

		; Initialize the main top
    ld hl, _OAMRAM
    ld a, 64 + 16
    ld [hli], a
    ld a, 96 + 8
    ld [hli], a
    ld a, 0
    ld [hli], a
    ld a, 0
    ld [hli], a
    ; Now initialize the main bottom
    ld a, 80 + 16
    ld [hli], a
    ld a, 96 + 8
    ld [hli], a
    ld a, 2
    ld [hli], a
    ld a, 0
    ld [hli], a

    ld a, 96 + 16
    ld [hli], a
    ld a, 96 + 8
    ld [hli], a
    ld a, 4
    ld [hli], a
    ld a, 0
    ld [hli], a
    ; Now initialize the main bottom
    ld a, 112 + 16
    ld [hli], a
    ld a, 96 + 8
    ld [hli], a
    ld a, 6
    ld [hli], a
    ld a, 0
    ld [hli], a
    ; The ball starts out going up and to the right
      
    

      ld a, 0
      ld [wGameOver], a
      ld [wMainMomentumX], a
      ld [wMainMomentumY], a
      ld [wMainMomentumX+1], a
      ld [wMainMomentumY+1], a
      ld [wMainX], a
      ld [wMainY], a
      ld [wScrollSpeed+1], a
      ld [wScrollCounter], a
      ld [wScrollCounter+1], a
      ld [wMainCost],a

      ld [wScary],a

      call InitNoteTable
      ld a, 1;1 pix per frame
      ld [wScrollSpeed], a
      ld a, cub
      ld [wMainType],a
      ld a,20
      ld [wMainX+1], a
      ld a,80
      ld [wMainY+1], a
      


    ; Turn the LCD on
    ld a, LCDCF_ON | LCDCF_BGON | LCDCF_OBJON | LCDCF_OBJ16 ; danielrh added
    ld [rLCDC], a

    ; turn on sound
    ld a, $80
    ld [rAUDENA], a
    ld a, $ff
    ld [rAUDTERM], a
    ld a, $77
    ld [rAUDVOL], a

    ; manage sound
    call SetSongBank
    ld hl , lvl1song
    call hUGE_init
    call InitNoteTable

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
    ld [wLastKeyDown], a
    ld a,1
    ld [wLevelSelector],a

  ret
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
    ld bc, MainSpaceRightEnd - MainLeft
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
      
    

      ld a, 0
      ld [wGameOver], a
      ld [wMainMomentumX], a
      ld [wMainMomentumY], a
      ld [wMainMomentumX+1], a
      ld [wMainMomentumY+1], a
      ld [wMainX], a
      ld [wMainY], a
      ld [wScrollSpeed+1], a
      ld [wScrollCounter], a
      ld [wScrollCounter+1], a
      ld [wMainCost],a
      ld a, 1;1 pix per frame
      ld [wScrollSpeed], a
      ld a, cub
      ld [wMainType],a
      ld a,20
      ld [wMainX+1], a
      ld a,80
      ld [wMainY+1], a
      


    ; Turn the LCD on
    ld a, LCDCF_ON | LCDCF_BGON | LCDCF_OBJON | LCDCF_OBJ16 ; danielrh added
    ld [rLCDC], a

    ; turn on sound
    ld a, $80
    ld [rAUDENA], a
    ld a, $ff
    ld [rAUDTERM], a
    ld a, $77
    ld [rAUDVOL], a

    ; manage sound
    call SetSongBank
    ld hl , lvl1song
    call hUGE_init
    call InitNoteTable

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

    ld a, [wGameOver]
    cp a, ($ff - $20) 
    jp c,gameb
    call reset
    gameb:

    ; Update the OAM
    ld a, [wMainY+1]
    add a, 16
    ld [_OAMRAM + 0],a
    ld [_OAMRAM + 4],a
    ; ld a, [wMainType]
    ; cp a, $29
    ; jp nz, spacestart
    ; ld a, [wMainAngle]
    
    ; srl a
    ; srl a
    ; srl a
    ; and a, 3
    ; add a, a
    ; add a, a
    ; jp spaceend
    ; spacestart:
    ; ;spaceship specific math; none yet.
    ; spaceend:
    ld a,[wMainCost]


    ld [_OAMRAM + 2],a
    inc a
    inc a
    ld [_OAMRAM + 6],a

    ld a, [wMainX+1]
    add a, 8
    ld [_OAMRAM + 1],a
    add a, 8
    ld [_OAMRAM + 5],a
    ; after vblank time
    call UpdateKeys

    ld a, [wCurKeys]
    and a, PADF_SELECT
    ret nz



    ld a, [wFrameCounter]
    inc a
    ld [wFrameCounter], a
    ld a, [wScrollCounter]
    ld l, a
    ld a, [wScrollCounter+1]
    ld h, a
    ld a, [wScrollSpeed]
    ld e, a
    ld a, [wScrollSpeed+1]
    ld d, a
    add hl, de
    ld a, h
    ld [wScrollCounter+1],a
    ld a, l
    ld [wScrollCounter],a
    ld [rSCX] ,a
    
    call ScrollLevel
    

    call SetSongBank
    call hUGE_dosound
    call CorruptNoteEntry
    call CorruptWaveRAM

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
    call Transporters
    ld a, [wGameOver]
    or a, 0
    jp z, gamea
    inc a
    ld [wGameOver], a
    gamea:
    call CheckGhostTile
    call CheckSpikeTile
    jp nz, nospike
    ld a, [wNoSpike]
    or a
    jp nz, nospike
    call GameOver
    nospike:



    call CheckPortalTile
    jp nz, noPortal
    ld [wMainType], a

    noPortal:
    


    ; Update the OAM
    ; ld a, [wMainY+1]
    ; add a, 16
    ; ld [_OAMRAM + 0],a
    ; ld [_OAMRAM + 4],a

    ; ld a, [wMainX+1]
    ; add a, 8
    ; ld [_OAMRAM + 1],a
    ; add a, 8
    ; ld [_OAMRAM + 5],a

    ; Add the ball's momentum to its position in OAM.
    
    ; First, check if the left button is pressed.
    

    
    
; Then check the right button.
    ld a, [wGameOver]
    cp a, $fe
    jp nz, .skipResetSong
    call SetSongBank
    ld hl , lvl1song
    call hUGE_init
    call InitNoteTable
    .skipResetSong
    jp Main



PlayerMovement:
  ld a,  [wMainType]
  cp a, rok
  jp z, SpaceMovement

  jp nz, CubeMovement
  ret

  CubeMovement:
  ld a,[wGameOver]
  cp a,0
  jp nz, .DoneTouchingGround
  ld e,$2e
  ld d,$00
  call Gravity
  call Turn
  
  ; check if touching the ground
  call CheckFloorTile
  ; if not touching ground, go to .DoneTouchingGround
  jp nz ,.DoneTouchingGround
    ; if Speed < 0 (bit 7 wMainMomentumY + 1) go to BonkedCeiling
    ld a, 0
    ld [wMainAngle], a
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

  SpaceMovement:
  ld e,ROCKETTHRUST
  ld d,$00
  call Gravity
  call clamp
  call SpaceTurn
  
  call CheckFloorTile
  jp nz ,.DoneTouchingGround
    ; if Speed < 0 (bit 7 wMainMomentumY + 1) go to BonkedCeiling
    
    ld a ,[wMainMomentumY+1]
    bit 7,a 
    jp nz ,.BonkedCeiling;neg
    ; Move Out Of Level with dy = -1 -> hl

    ld h, $ff
    ld l, $00
    call MoveOutofLevel

  .DoneTouchingGround:
  call CheckUp
  ret
  .BonkedCeiling:
  ld h, $02
  ld l, $00
  call MoveOutofLevel
  call CheckUp
  ret
  
  clamp:
  ld a, [wMainMomentumY]
  ld l, a
  ld a, [wMainMomentumY+1]
  ld h, a
  bit 7,a
  jp nz, upclamp
  ld a, l
  cp a, ROCKETUPCLAMP
  jp c, clampdone
  ld l, ROCKETUPCLAMP

  jp clampdone
  upclamp:

  ld a, l
  cp a, ROCKETDOWNCLAMP
  jp nc, clampdone
  ld l, ROCKETDOWNCLAMP

  clampdone:


  ld a, l
  ld [wMainMomentumY],a
  ld a, h
  ld [wMainMomentumY+1], a
  ret

  SpaceTurn:
  ld a, [wMainMomentumY]
  cp a, $d0
  jp nc, .cos3
  cp a, $b0
  jp nc, .cos2
  cp a, $a0
  jp nc, .cos1
  cp a, $80
  jp nc, .cos0
  cp a, $60
  jp nc, .cos6
  cp a, $50
  jp nc, .cos5
  cp a, $30
  jp nc, .cos4
  .cos3:
  ld a, $1c
  ld [wMainCost],a
  ret
  .cos2:
  ld a, $18
  ld [wMainCost],a
  ret
  .cos1:
  ld a, $14
  ld [wMainCost],a
  ret
  .cos0:
  .cos6:
  ld a, [wMainMomentumY+1]
  or a, a
  jp nz, .fixme0
  ld a, $28
  ld [wMainCost],a
  ret
  .fixme0:
  ld a, $10
  ld [wMainCost],a
  ret
  .cos5:
  ld a, $24
  ld [wMainCost],a
  ret
  .cos4:
  ld a, $20
  ld [wMainCost],a
  ret
  
    

  ; smart way
  cp a, $80
  srl a
  srl a
  srl a
  srl a
  srl a
  jp c ,.c
  add a, 7
  add a, a
  add a, a
  ld [wMainAngle],a
  ret
  .c:
  add a, 4
  add a, a
  add a, a
  ld [wMainAngle],a
  ret



INCLUDE "func.asm"

INCLUDE "util.asm"

INCLUDE "tiles.asm"

INCLUDE "sprites.asm"

INCLUDE "level.asm"

INCLUDE "levelmusic.asm"

INCLUDE "level2.asm"
INCLUDE "level3.asm"
INCLUDE "level4.asm"

;INCLUDE "level2music.asm"

INCLUDE "menulevel.asm"
;INCLUDE "menumusic.asm"

INCLUDE "spooky.asm"

INCLUDE "var.asm"
