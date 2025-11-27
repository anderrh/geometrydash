SECTION "Time", WRAM0
wFrameCounter: db
wScrollCounterLow: dw
wScrollCounterHigh: dw
wScrollSpeedLow: dw
wScrollSpeedHigh: dw


SECTION "Input Variables", WRAM0
wCurKeys: db
wNewKeys: db

SECTION "Main Data", WRAM0
wMainX: dw
wMainY: dw
wMainMomentumY: dw
wMainMomentumX: dw
WMainAngle:dw

SECTION "Score", WRAM0
wScore: db