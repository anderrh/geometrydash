SECTION "Time", WRAM0
wFrameCounter: db
wScrollCounter: dw
wScrollSpeed: dw

SECTION "Input Variables", WRAM0
wCurKeys: db
wNewKeys: db

SECTION "Main Data", WRAM0
wMainX: dw
wMainY: dw
wMainMomentumY: dw
wMainMomentumX: dw
wMainAngle:dw

SECTION "Score", WRAM0
wScore: db
wGameOver:db