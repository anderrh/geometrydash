CheckFloorTile:

    ld a, [wMainX+1]
    ld b, a
    ld a, [wMainY+1]
    add a, 3
    ld c,a
    call GetTilesByAPixel
    ld a, b
    call IsFloorTile
    ret z
    ld a, c
    call IsFloorTile
    ret z
    ld a, d
    call IsFloorTile
    ret z
    ld a, e
    call IsFloorTile
    ret

CheckPortalTile:

    ld a, [wMainX+1]
    ld b, a
    ld a, [wMainY+1]
    add a, 3
    ld c,a
    call GetTilesByAPixel
    ld a, b
    call GetPortalTile
    ret z
    ld a, c
    call GetPortalTile
    ret z
    ld a, d
    call GetPortalTile
    ret z
    ld a, e
    call GetPortalTile
    ret

GetPortalTile:
    cp a, $25
    ret z
    cp a, $29
    ret z
    ld a, 0
    ret

IsCubePortalTile:
    cp a, $29
    ret 

IsSpacePortalTile:
    cp a, $25
    ret 





reset:
    ld a, 1 ; 1 pixel per frame scrolling
    ld [wScrollSpeed], a
    ld a, 0
    ld [rSCX] ,a

    ld a, 0
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

    ld a, cub
    ld [wMainType],a

    ld a,80
    ld [wMainY+1], a
    ld a,20
    ld [wMainX+1], a

    ld b ,0
    ld de, 0
    ld hl, 0
    ld a, [wGameOver]
    sub a, ($ff - $20)
    ld c, a
    ld e, c
    ld l, c
    call CopyColumn
    call SetSongBank
    ld a, 0
    ld c , 1
    call hUGE_set_position
    ret
IsFloorTile:
    cp a, $11
    ret z
    cp a, $21
    ret z
    cp a, $22
    ret 
GetTilesByAPixel:
    call GetLevelTileAddressFromScroll
    ; address of left tile is in hl

    ld a, [hli]
    ; sub l, 
    ld b, a
    ld a, [hl]
    ld c, a
    ld de, 31
    add hl, de
    ld a, [hli]
    ld d, a
    ld a, [hl]
    ld e, a
    ret

CheckSpikeTile:

    ld a, [wMainX+1]
    add a, 7
    ld b, a
    ld a, [wMainY+1]
    add a, 7
    ld c,a
    call GetTileByPixel
    ld a, [hl]
    call IsSpikeTile
    ret
    ret

IsSpikeTile:
    cp a, $12
    ret z
    cp a, $13
    ret z
    cp a, $14
    ret z
    cp a, $15
    ret z
    cp a, $16
    ret 


CheckUp:
    ld a, [wCurKeys]
    and a, PADF_UP
    ld b, a
    ld a, [wCurKeys]

    and a, PADF_A
    or a, b
    ret z
Up:
    ld a, [wMainType]
    cp a,rok
    jp z, .rocket
    ld a, $00
    ld [wMainMomentumY], a
    ld a, $fd
    ld [wMainMomentumY+1], a
    ret
    .rocket:
    ld a, [wMainMomentumY]
    ld l,a
    ld a, [wMainMomentumY+1]
    ld h,a
  
  
    ld e,$ff - 2* ROCKETTHRUST + $1
    ld d,$ff
;  bit 7, h ; if negative always do gravity
;  jp nz, .always_do_gravity
;  ld a, h
;  cp a, 4
;  jp nc, .skip_terminal_velocity
;  .always_do_gravity:
    add hl, de
;.skip_terminal_velocity:
    ld a,l
    ld [wMainMomentumY], a
    ld a,h
    ld [wMainMomentumY+1], a
    ret

Gravity:
;arg e
;arg d
  ld a, [wMainMomentumY]
  ld l,a
  ld a, [wMainMomentumY+1]
  ld h,a
  
  
  
;  bit 7, h ; if negative always do gravity
;  jp nz, .always_do_gravity
;  ld a, h
;  cp a, 4
;  jp nc, .skip_terminal_velocity
;  .always_do_gravity:
  add hl, de
;.skip_terminal_velocity:
  ld a,l
  ld [wMainMomentumY], a
  ld a,h
  ld [wMainMomentumY+1], a
  ret


MoveOutofLevel:
    ; Please place dy (1 or -1) into hl
    ; and this will modify wMainMomentumY and wMainY
    ; So it is no longer in the level
    push de
    push af
    push bc
    push hl
    ; add hl, hl;multiply by 2
    ; griffpatch only add hl, hl;multiply by 4
    call Neg16
    ; now we need to load wMainY into de and then hl = hl + de
    ; and then write hl back to wMainY
    ld a,[wMainY]
    ld e, a
    ld a,[wMainY + 1]
    ld d, a
    add hl, de
    ld a, l
    ld [wMainY], a
    ld a, h
    ld [wMainY + 1], a
    ;this is loop setup to get our counter bc setup to be |mMomentumY| + 8
    ld a, 0
    ld h, a
    ld a, [wMainMomentumY+1]
    ld l, a
    call Abs16
    ld e, $02
    ld d, $00
    add hl, de
    ld b,h
    ld c,l
    ld a,0
    ld [wMainMomentumY], a
    ld [wMainMomentumY+1], a
    ; now lets begin the loop
    .repeat_abs_speedY_8:
        pop hl
        push hl
        ; we saved hl at the top of the stack; grab it.
        ld a,[wMainY]
        ld e, a
        ld a,[wMainY + 1]
        ld d, a
        add hl, de ; [wMainY] = [wMainY] + dy
        ld a, l
        ld [wMainY], a
        ld a, h
        ld [wMainY + 1], a
        push bc
        call CheckFloorTile
        pop bc
        ; if it's a floor tile then z flag is set
        jp z ,.Touching
        ; not Touching code here
        
        jp .StopThisScript
        .Touching:
        dec bc
        ld a, b
        or a, c
        jp nz, .repeat_abs_speedY_8
    ; die
    pop hl
    push hl
    add hl, hl
    add hl, hl;multiply by 4
    call Neg16
    ; now we need to load wMainY into de and then hl = hl + de
    ; and then write hl back to wMainY
    ld a,[wMainY]
    ld e, a
    ld a,[wMainY + 1]
    call GameOver

    .StopThisScript
    pop hl
    pop bc
    pop af
    pop de
    ret

GameOver:
    ld a, [wGameOver]
    or a
    jp nz, .nza
    ld a, $7f
    .nza:
    ld [wGameOver],a
    ld a, 0
    ld [wScrollSpeed],a
    ld [wScrollSpeed+1],a
    
    ret
Turn:
    ld a, [wMainAngle]
    inc a
    ld [wMainAngle], a 
    srl a
    srl a
    srl a
    and a, 3
    add a, a
    add a, a
    ld [wMainCost],a
    ret
ScrollLevel:
; 00000111 | 10101000
;           &00000011 = 0 so we're good 
; what we want isl
;   000001 | 11101010 (don't want 00)

; 0, 1, 2, 3, 4, 5, 6
    ld a, [wScrollCounter]
    and 7
    ret nz
; 0, 4, 8, 12 
    ld a, [wScrollCounter]
    ld e,a
    ld a, [wScrollCounter+1]
    ld d,a
    srl d
    rr e
    srl d
    rr e
    srl d
    rr e ;shift de 2 times
    ld hl, 31 ;source
    add hl, de;<-------------J (now it's column scroll + 31)
    ld de, 31 ;DEstanation
    ld a, [rSCX]
    srl a
    srl a
    srl a
    add a, e
    and a, 31
    ld e, a
    ld d, 0
    call CopyColumn
    ret


CopyColumn:
; the column destination number from 0-31 is in de
; the column source is in hl from 0 to LevelWidth.
;     Remember to multiply hl by 32 to get the offset into Level
    
    push bc
    push de
    push af
    push hl
    
    ld hl, _SCRN0
    add hl, de
    ld c, l
    ld b, h ; destination memory in BC
    pop hl
    push hl
    ; remember multiply hl by 32
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld de, Level
    add hl, de
    ld d, b
    ld e, c
    ld c, levelHeight  

    
    call SetLevelBank
    ; dest in [de]
    ; src in [hl]
    ; num to copy in c
    .StartCopying:
        ;loop for copying
        ld a, [hli]
        ld [de], a
        ld a, $20
        add a, e
        ld e,a
        ld a, 0
        adc a, d
        ld d, a
        dec c
        jp nz ,.StartCopying
    ld a, 0
    ld [rROMB0],a
    

    


     pop hl
     pop af 
     pop bc
     pop de
    ret

Transporters:

    ld a, [wMainX+1]
    ld b, a
    ld a, [wMainY+1]
    add a, 3
    ld c,a
    call GetTilesByAPixel
    call CheckBouncers
    jp nz, .noBounceUp
    ld a, $fb
    ld [wMainMomentumY+1], a
    ld a, $00
    ld [wMainMomentumY], a
    
    .noBounceUp:

    ret
CheckBouncers:
    ld a, b
    cp a, $17
    ret z
    ld a, c
    cp a, $17
    ret
SetSongBank:
    ld a , [wLevel]
    add a, a
    inc a
    ld [rROMB0], a
    ret

SetLevelBank:
    ld a , [wLevel]
    inc a
    add a, a
    ld [rROMB0], a
    ret

























































;This game was  made by a guy called Ander which witch wanted werid wonky whips ? did you know Baba and Mama are the best people in the world I like to play the piano with super style thrust bounce baby rock bro hey hat nah nose bro dis ti de b do. cu u no ih do ba doh crit.
