CheckFloorTile:
    ;clobbers 
    ; a, f, h, l, b ,c
    ld a, [wMainX+1]
    ld b, a
    ld a, [wMainY+1]
    ld c, a
    call GetTileByPixel
    call IsFloorTile
    ret z
    ld a,b
    add a, 8
    ld b,a
    call GetTileByPixel
    call IsFloorTile
    ret z
    ld a,c
    add a, 8
    ld c,a
    call GetTileByPixel
    call IsFloorTile
    ret z
    ld a,b
    sub a, 8
    ld b,a
    call GetTileByPixel
    call IsFloorTile
    ret
IsFloorTile:
    ld a, [hl]
    cp a, 11
    ret z
    cp a, 20
    ret z
    cp a, 21
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
    
    ld a, $ff
    ld [wMainMomentumY], a
    ld a, $fd
    ld [wMainMomentumY+1], a
    ret

Gravity:
  ld a, [wMainMomentumY]
  ld l,a
  ld a, [wMainMomentumY+1]
  ld h,a
  
  
  ld e,$38
  ld d,$00

  add hl, de

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
    add hl, hl
    add hl, hl;multiply by 4
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
