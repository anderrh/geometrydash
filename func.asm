CheckFloorTile:
    ;clobbers 
    ; a, f, h, l, b ,c
    ;ld a, [wMainX+1]
    ;ld b, a
    ;ld a, [wMainY+1]
    ;ld c, a
    ;ld a,c
    ;add a, 4
    ;ld c,a
    ;call GetTileByPixel
    ;call IsFloorTile
    ;ret z
    ;ld a, [wMainX+1]
    ;ld b, a
    ;ld a, [wMainY+1]
    ;ld c, a
    ;ld a,b
    ;add a, 8
    ;ld b,a
    ;ld a,c
    ;add a, 4
    ;ld c,a
    ;call GetTileByPixel
    ;call IsFloorTile
    ;ret z
    ld a, [wMainX+1]
    ld b, a
    ld a, [wMainY+1]
    ld c, a
    ld a,c
    add a, 11
    ld c,a
    call GetTileByPixel
    call IsFloorTile
    ret z
    ld a, [wMainX+1]
    ld b, a
    ld a, [wMainY+1]
    ld c, a
    ld a,b
    add a, 8
    ld b,a
    ld a,c
    add a, 11
    ld c,a
    call GetTileByPixel
    call IsFloorTile
    ret
IsFloorTile:
    ld a, [hl]
    cp a, $11
    ret z
    cp a, $20
    ret z
    cp a, $21
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
    
    ld a, $f0
    ld [wMainMomentumY], a
    ld a, $fd
    ld [wMainMomentumY+1], a
    ret

Gravity:
  ld a, [wMainMomentumY]
  ld l,a
  ld a, [wMainMomentumY+1]
  ld h,a
  
  
  ld e,$30
  ld d,$00
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
    ld a, [wMainMomentumY]
    ld l, a
    ld a, [wMainMomentumY+1]
    ld h, a
    call Abs16
    ld e, $08
    ld d, $00
    add hl, de
    ld b,h
    ld c,l
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
        ld a,0
        ld [wMainMomentumY], a
        ld [wMainMomentumY+1], a
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
    ld a, 1
    ld [wGameOver],a
    ld a, 0
    ld [wScrollSpeedLow],a
    ld [wScrollSpeedLow+1],a
    ld [wScrollSpeedHigh],a
    ld [wScrollSpeedHigh+1],a
    ret
Turn:
    ret
ScrollLevel:
; 00000111 | 10101000
;           &00000011 = 0 so we're good 
; what we want isl
;   000001 | 11101010 (don't want 00)

; 0, 1, 2, 3, 4, 5, 6
    ld a, [wScrollCounterLow]
    and 3
    ret nz
; 0, 4, 8, 12 
    ld a, [wScrollCounterLow]
    ld e,a
    ld a, [wScrollCounterLow+1]
    ld d,a
    srl d
    rr e
    srl d
    rr e ;shift de 2 times
    ld hl, (Level + 31) ;source
    add hl, de;<-------------J
    ld de, (_SCRN0+31) ;DEstanation
    ld a, [rSCX]
    srl a
    srl a
    srl a
    add a, e
    ld e, a
    ld a, 0
    adc a, d
    ld d, a
    
    ld c, levelHeight       ;|
    .levelcopy:
    
    ld a, [hl];_SCRN0 is tilemap5! width SCRN_X_B
    ld [de], a

    ld a,low(levelWidth)
    add a,l
    ld l,a
    ld a,high(levelWidth)
    adc a, h
    ld h, a

    ld a,$20
    add a,e
    ld e,a
    ld a,0
    adc a, d
    ld d, a

    dec c
    jp nz, .levelcopy

    ret


CopyColumn:
    
    push bc
    push de
    push af
    push hl
    
    ld a low((_SCRN0))
    ld l,a
    ld a,high((_SCRN0))
    ld h,a
    add de, hl
    ld bc,hl
    pop hl
    push hl
    ld a, low(Level)
    ld e, a
    ld a, high(Level)
    ld d, a
    add de ,hl
    ;dest in bc
    ;src in hde




; the column 0 ... level-1 is in hl
; de should 
; the column destination number from 0-31 is in de
    .StartCopying:
        ;loop for copying





; ; 0, 1, 2, 3, 4, 5, 6
;     ld a, [wScrollCounterLow]
;     and 3
;     ret nz
; ; 0, 4, 8, 12 
;     ld a, [wScrollCounterLow]
;     ld e,a
;     ld a, [wScrollCounterLow+1]
;     ld d,a
;     srl d
;     rr e
;     srl d
;     rr e ;shift de 2 times
;     ld hl, (Level + 31) ;source
;     add hl, de;<-------------J
;     ld de, (_SCRN0+31) ;DEstanation
;     ld a, [rSCX]
;     srl a
;     srl a
;     srl a
;     add a, e
;     ld e, a
;     ld a, 0
;     adc a, d
;     ld d, a
    
;     ld c, levelHeight       ;|
;     .levelcopy:
    
;     ld a, [hl];_SCRN0 is tilemap5! width SCRN_X_B
;     ld [de], a

;     ld a,low(levelWidth)
;     add a,l
;     ld l,a
;     ld a,high(levelWidth)
;     adc a, h
;     ld h, a

;     ld a,$20
;     add a,e
;     ld e,a
;     ld a,0
;     adc a, d
;     ld d, a

;     dec c
;     jp nz, .levelcopy
     pop hl
     pop af 
     pop bc
     pop de
    ret