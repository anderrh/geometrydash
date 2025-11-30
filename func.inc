CheckFloorTile:
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