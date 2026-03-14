#!/usr/bin/env python3
"""Generate a challenging level2.asm for the Geometry Dash game."""

# Grid: 512 columns x 32 rows
# Rows 0-16: playable area (0=top, 16=ground surface)
# Rows 17-31: always BBB (underground)
# Player starts at bottom, standing on row 16

COLS = 512
ROWS = 32
PLAY_ROWS = 17  # 0-16
GROUND_ROWS = 15  # 17-31

# Tile constants
o = "ooo"  # sky/empty
B = "BBB"  # solid block
A = "AAA"  # spike (up)
v = "vvv"  # spike (variant)
i = "iii"  # spike/pillar
I = "III"  # spike/light
u = "uuu"  # spike/surface
BOUNCE = "$17"
FLOOR1 = "$21"  # alternate floor
FLOOR2 = "$22"  # alternate floor
DECO_A = "$1a"
DECO_B = "$1b"

# Portals (3 wide, 2 tall)
ROCKET_ON_TOP = ["$23", "$25", "$27"]
ROCKET_ON_BOT = ["$24", "$26", "$28"]
ROCKET_OFF_TOP = ["$23", "$29", "$27"]
ROCKET_OFF_BOT = ["$24", "$26", "$28"]

def make_grid():
    """Create empty grid with ground."""
    grid = []
    for col in range(COLS):
        column = [o] * PLAY_ROWS + [B] * GROUND_ROWS
        grid.append(column)
    return grid

def set_tile(grid, col, row, tile):
    if 0 <= col < COLS and 0 <= row < ROWS:
        grid[col][row] = tile

def set_ground(grid, col, height, width=1):
    """Place ground at given height (row index). Fill from height down to row 16."""
    for c in range(col, min(col + width, COLS)):
        for r in range(height, PLAY_ROWS):
            grid[c][r] = B

def set_platform(grid, col, row, width=1, height=1):
    """Place a platform (BBB blocks)."""
    for c in range(col, min(col + width, COLS)):
        for r in range(row, min(row + height, PLAY_ROWS)):
            grid[c][r] = B

def set_spike(grid, col, row, spike_type=A):
    """Place a spike."""
    set_tile(grid, col, row, spike_type)

def set_bouncer(grid, col, row):
    set_tile(grid, col, row, BOUNCE)

def place_rocket_on(grid, col, row):
    """Place rocket-ON portal at (col, row) - 2 wide, 3 tall.
    Col1: $23, $25, $27 (top to bottom)
    Col2: $24, $26, $28 (top to bottom)"""
    set_tile(grid, col, row, "$23")
    set_tile(grid, col, row + 1, "$25")
    set_tile(grid, col, row + 2, "$27")
    set_tile(grid, col + 1, row, "$24")
    set_tile(grid, col + 1, row + 1, "$26")
    set_tile(grid, col + 1, row + 2, "$28")

def place_rocket_off(grid, col, row):
    """Place rocket-OFF portal at (col, row) - 2 wide, 3 tall.
    Col1: $23, $29, $27 (top to bottom)
    Col2: $24, $26, $28 (top to bottom)"""
    set_tile(grid, col, row, "$23")
    set_tile(grid, col, row + 1, "$29")
    set_tile(grid, col, row + 2, "$27")
    set_tile(grid, col + 1, row, "$24")
    set_tile(grid, col + 1, row + 1, "$26")
    set_tile(grid, col + 1, row + 2, "$28")

def place_wall(grid, col, top_row, bottom_row, width=1):
    """Place a wall from top_row to bottom_row."""
    for c in range(col, min(col + width, COLS)):
        for r in range(top_row, min(bottom_row + 1, PLAY_ROWS)):
            grid[c][r] = B

def place_deco(grid, col, row):
    """Place decorative pillar pair."""
    set_tile(grid, col, row, DECO_A)
    set_tile(grid, col + 1, row, DECO_B)

def generate_level():
    grid = make_grid()

    # DESIGN RULES:
    # - Max reliable jump = 2 blocks high
    # - Max spikes in a row = 3
    # - All spikes must have solid block underneath
    # - Rocket corridors min 4 tiles open (ship=2 + wiggle=2)
    # - Rocket entrance: at ground level, obvious and easy to enter
    # - Rocket exit: unavoidable (walls funnel into it)
    # - Bouncer walls: max ~4 blocks high above ground, or use sequential pads

    # Helper: spike on ground (spike at row, block underneath at row+1..16)
    def ground_spike(col, row, typ=A):
        """Place spike with solid ground beneath it."""
        set_spike(grid, col, row, typ)
        for r in range(row + 1, PLAY_ROWS):
            grid[col][r] = B

    # === SECTION 1: Opening (cols 0-9) - flat ground ===
    for c in range(0, 10):
        grid[c][16] = B

    # === SECTION 2: First jumps with spikes (cols 10-44) ===
    for c in range(10, 48):
        grid[c][16] = B

    # Single spike
    ground_spike(14, 15)

    # Double spike with gap
    ground_spike(20, 15)
    ground_spike(21, 15, v)

    # Triple spike (max allowed)
    ground_spike(28, 15)
    ground_spike(29, 15, v)
    ground_spike(30, 15)

    # Block (1 high) + spike on top
    set_platform(grid, 35, 15, width=2, height=2)
    ground_spike(35, 14)
    ground_spike(36, 14, v)

    # Single spike then gap in ground (pit)
    ground_spike(40, 15)
    for c in range(42, 45):
        grid[c][16] = o  # pit

    # === SECTION 3: Staircase up (cols 48-85) - max 2 block steps ===
    for c in range(48, 52):
        grid[c][16] = B
    ground_spike(51, 15)

    # Step up 2 blocks: ground at row 14
    set_platform(grid, 54, 14, width=5, height=3)
    ground_spike(53, 15)
    ground_spike(59, 13, v)

    # Step up 2 more: ground at row 12
    set_platform(grid, 62, 12, width=5, height=5)
    ground_spike(61, 13)

    # Step up 2 more: ground at row 10
    set_platform(grid, 69, 10, width=5, height=7)
    ground_spike(68, 11, v)

    # Descend: step down 2 to row 12
    set_platform(grid, 76, 12, width=4, height=5)
    ground_spike(75, 11)
    ground_spike(80, 11, v)

    # Step down 2 to row 14
    set_platform(grid, 82, 14, width=4, height=3)
    ground_spike(81, 13)

    # Back to ground
    for c in range(87, 92):
        grid[c][16] = B
    ground_spike(86, 15)

    # === SECTION 4: Pillars with ground spikes (cols 92-125) ===
    for c in range(92, 128):
        grid[c][16] = B

    # Ground spikes
    ground_spike(94, 15)
    ground_spike(95, 15, v)
    ground_spike(99, 15)

    # Pillar 1: wall from row 12 to 16 - needs bouncer to clear
    set_bouncer(grid, 101, 15)
    place_wall(grid, 103, 12, 16, width=2)
    ground_spike(103, 11)
    ground_spike(104, 11, v)

    # Gap at 105-106
    ground_spike(106, 15)

    # Pillar 2: shorter wall (row 14) - can normal jump onto it
    place_wall(grid, 109, 14, 16, width=3)

    # Pillar 3: wall from row 12 to 16 - normal jump from pillar 2 clears it
    place_wall(grid, 114, 12, 16, width=2)
    #ground_spike(114, 11)

    # After pillars, ground with spikes
    ground_spike(120, 15)
    ground_spike(121, 15, v)
    ground_spike(125, 15)

    # === SECTION 5: Bouncer section (cols 128-170) ===
    for c in range(128, 175):
        grid[c][16] = B

    # Bouncer + low wall (4 blocks above ground = rows 12-16)
    set_bouncer(grid, 131, 15)
    place_wall(grid, 134, 12, 16, width=2)
    ground_spike(134, 11)
    # Landing area
    ground_spike(137, 15)

    # Double bouncer for higher wall
    set_bouncer(grid, 141, 15)
    set_bouncer(grid, 143, 15)
    place_wall(grid, 146, 10, 16, width=2)
    ground_spike(146, 9, v)

    # Landing platform at row 12 (safe descent)
    set_platform(grid, 149, 12, width=4, height=5)
    ground_spike(153, 11)

    # Bouncer + wall + spike
    set_bouncer(grid, 156, 15)
    place_wall(grid, 159, 12, 16, width=2)
    ground_spike(159, 11)

    # Another double bouncer for bigger wall
    set_bouncer(grid, 163, 15)
    set_bouncer(grid, 165, 15)
    place_wall(grid, 168, 10, 16, width=2)
    ground_spike(168, 9, v)

    # Descend safely
    set_platform(grid, 171, 12, width=3, height=5)

    # === SECTION 6: Rocket entrance (cols 175-200) ===
    # Ground level, portal is obvious and right in the path
    for c in range(175, 205):
        grid[c][16] = B

    ground_spike(177, 15)
    ground_spike(178, 15, v)

    # Small platform for visual interest
    set_platform(grid, 182, 14, width=3, height=3)
    ground_spike(182, 13)
    ground_spike(184, 13, v)

    # Portal raised 2 blocks above ground (requires a jump)
    # Portal at row 12-14, cols 191-192
    place_rocket_on(grid, 191, 12)

    # === SECTION 7: Rocket maze (cols 192-335) ===
    # All corridors have minimum 4 tiles of open space
    # Ship is 2 tiles, plus 1 above and 1 below for wiggle

    # Opening corridor - wide to ease into rocket mode
    # 8 columns of open air after portal before tunnel walls
    for c in range(200, 210):
        place_wall(grid, c, 0, 3)    # ceiling (rows 0-3)
        place_wall(grid, c, 12, 16)  # floor (rows 12-16)
    # Open: rows 4-11 = 8 tiles (very comfortable)

    # Gradual narrowing
    for c in range(210, 225):
        place_wall(grid, c, 0, 4)    # ceiling (rows 0-4)
        place_wall(grid, c, 11, 16)  # floor (rows 11-16)
    # Open: rows 5-10 = 6 tiles

    # Spike tunnel - spikes on walls, 6 tile corridor
    for c in range(225, 245):
        place_wall(grid, c, 0, 3)    # ceiling
        place_wall(grid, c, 11, 16)  # floor
    # Open: rows 4-10 = 7 tiles
    # Alternating ceiling/floor spikes (attached to walls)
    for c in range(227, 244, 3):
        set_spike(grid, c, 4, u)     # hangs from ceiling block at row 3
        set_spike(grid, c+1, 10, A)  # sits on floor block at row 11

    # S-curve UP: passage shifts upward
    for c in range(245, 253):
        place_wall(grid, c, 0, 1)    # thin ceiling
        place_wall(grid, c, 7, 16)   # high floor
    # Open: rows 2-6 = 5 tiles

    # Transition columns (gradual shift)
    for c in range(253, 257):
        place_wall(grid, c, 0, 2)
        place_wall(grid, c, 9, 16)
    # Open: rows 3-8 = 6 tiles

    # S-curve DOWN: passage shifts downward
    for c in range(257, 265):
        place_wall(grid, c, 0, 5)    # low ceiling
        place_wall(grid, c, 11, 16)  # low floor
    # Open: rows 6-10 = 5 tiles

    # Wide section with pillar obstacles
    for c in range(265, 285):
        place_wall(grid, c, 0, 2)    # thin ceiling
        place_wall(grid, c, 12, 16)  # floor
    # Open: rows 3-11 = 9 tiles
    # Pillars in passage (leave 4+ tiles open above and below)
    place_wall(grid, 270, 5, 7)   # pillar, go above (rows 3-4 open) or below (rows 8-11 open)
    place_wall(grid, 275, 7, 9)   # pillar, go above (rows 3-6 open) or below (rows 10-11 open=5)
    place_wall(grid, 280, 4, 6)   # pillar, go below (rows 7-11 open=5)

    # Alternating passage with middle walls
    for c in range(285, 305):
        place_wall(grid, c, 0, 2)
        place_wall(grid, c, 13, 16)
    # Open: rows 3-12 = 10 tiles
    # Middle walls force up/down movement
    for c in range(288, 292):
        place_wall(grid, c, 7, 9)   # go above (rows 3-6=4) or below (rows 10-12=3+1=4)
    for c in range(296, 300):
        place_wall(grid, c, 5, 7)   # go above (rows 3-4=2+wiggle) or below (rows 8-12=5)
    for c in range(303, 307):
        place_wall(grid, c, 8, 10)  # go above (rows 3-7=5) or below (rows 11-12=2+wiggle)

    # Narrowing for tension
    for c in range(308, 320):
        place_wall(grid, c, 0, 4)
        place_wall(grid, c, 11, 16)
    # Open: rows 5-10 = 6 tiles
    # Single block obstacles
    set_tile(grid, 312, 7, B)
    set_tile(grid, 316, 8, B)

    # Widen out approaching exit
    for c in range(320, 332):
        place_wall(grid, c, 0, 3)
        place_wall(grid, c, 12, 16)
    # Open: rows 4-11 = 8 tiles

    # Last obstacle before exit
    place_wall(grid, 325, 6, 8)  # pillar, go above or below (4+ tiles each side)

    # === SECTION 8: Rocket exit - UNAVOIDABLE (cols 332-345) ===
    # Gradual funnel: ceiling lowers over several columns
    for c in range(332, 336):
        place_wall(grid, c, 0, 6)    # ceiling starts lowering
        place_wall(grid, c, 16, 16)
    for c in range(336, 340):
        place_wall(grid, c, 0, 8)    # ceiling lower
        place_wall(grid, c, 16, 16)
    for c in range(340, 344):
        place_wall(grid, c, 0, 10)   # ceiling gets low
        place_wall(grid, c, 14, 16)  # floor rises a bit
    # Open: rows 11-13 = 3 rows, plus portal is 3 tall
    # Place exit portal in the funnel - wide enough to fly through
    place_rocket_off(grid, 342, 11)
    # Wall after portal blocks flying over
    for c in range(345, 348):
        place_wall(grid, c, 0, 10)
        place_wall(grid, c, 14, 16)

    # Landing zone after exiting rocket - ground with room
    for c in range(348, 358):
        grid[c][16] = B

    # === SECTION 9: Post-rocket warmup (cols 358-380) ===
    for c in range(358, 508):
        grid[c][16] = B

    # Easy spikes to get back into cube rhythm
    ground_spike(360, 15)
    ground_spike(365, 15, v)
    ground_spike(366, 15)

    ground_spike(372, 15)
    ground_spike(373, 15, v)

    # === SECTION 10: Half-platform playground (cols 380-460) ===
    # Uses $21 half-platforms for visual variety
    # Player chooses between HIGH path (bouncer) or LOW path (spikes)

    # --- Choice 1 (cols 380-400): Bouncer high road vs spike low road ---
    # LOW PATH: ground with spikes
    ground_spike(383, 15)
    ground_spike(384, 15, v)
    ground_spike(388, 15)
    # Floating half-platforms as stepping stones (high road)
    set_tile(grid, 382, 12, FLOOR1)
    set_tile(grid, 383, 12, FLOOR1)
    set_tile(grid, 385, 12, FLOOR1)
    set_tile(grid, 386, 12, FLOOR1)
    set_tile(grid, 388, 12, FLOOR1)
    set_tile(grid, 389, 12, FLOOR1)
    # Bouncer to reach high road
    set_bouncer(grid, 380, 15)
    # Both paths merge at col 392
    set_platform(grid, 392, 14, width=4, height=3)

    # --- Choice 2 (cols 398-418): High spikes vs low spikes ---
    # LOW PATH: ground level, spike on ground
    ground_spike(400, 15)
    ground_spike(401, 15, v)
    # Half-platforms hovering at row 12 (high path)
    set_tile(grid, 399, 12, FLOOR1)
    set_tile(grid, 400, 12, FLOOR1)
    set_tile(grid, 401, 12, FLOOR1)
    set_tile(grid, 402, 12, FLOOR1)
    # Spike on high path entrance
    ground_spike(399, 11)
    # Bouncer for high path
    set_bouncer(grid, 397, 15)
    # Landing zone with half-platforms
    set_tile(grid, 405, 14, FLOOR1)
    set_tile(grid, 406, 14, FLOOR1)
    set_tile(grid, 407, 14, FLOOR1)
    set_tile(grid, 408, 14, FLOOR1)
    ground_spike(405, 15)
    # Safe ground after
    ground_spike(411, 15, v)

    # --- Floating half-platform staircase (cols 415-435) ---
    # Ascending half-platforms with generous landing
    set_tile(grid, 415, 15, FLOOR1)
    set_tile(grid, 416, 15, FLOOR1)
    set_tile(grid, 417, 15, FLOOR1)

    set_tile(grid, 420, 13, FLOOR1)
    set_tile(grid, 421, 13, FLOOR1)
    set_tile(grid, 422, 13, FLOOR1)

    set_tile(grid, 425, 11, FLOOR1)
    set_tile(grid, 426, 11, FLOOR1)
    set_tile(grid, 427, 11, FLOOR1)

    # Descending back down
    set_tile(grid, 430, 13, FLOOR1)
    set_tile(grid, 431, 13, FLOOR1)
    set_tile(grid, 432, 13, FLOOR1)

    set_tile(grid, 435, 15, FLOOR1)
    set_tile(grid, 436, 15, FLOOR1)
    set_tile(grid, 437, 15, FLOOR1)

    # Ground spikes under the floating platforms for danger
    ground_spike(419, 15)
    ground_spike(424, 15, v)
    ground_spike(429, 15)
    ground_spike(434, 15, v)

    # --- Choice 3 (cols 440-460): Final split ---
    # LOW: ground with triple spike
    ground_spike(443, 15)
    ground_spike(444, 15, v)
    ground_spike(445, 15)
    # HIGH: bouncer to half-platform bridge
    set_bouncer(grid, 441, 15)
    set_tile(grid, 444, 11, FLOOR1)
    set_tile(grid, 445, 11, FLOOR1)
    set_tile(grid, 446, 11, FLOOR1)
    set_tile(grid, 447, 11, FLOOR1)
    set_tile(grid, 448, 11, FLOOR1)
    # Merge point - wide safe landing
    set_platform(grid, 450, 14, width=5, height=3)

    # Short ground section
    ground_spike(457, 15)
    ground_spike(458, 15, v)

    # === SECTION 11: Victory lap (cols 460-508) ===
    # Gentle floating half-platforms leading to the end

    # A few ground spikes
    ground_spike(462, 15)
    ground_spike(467, 15, v)

    # Half-platform bridge over spikes
    set_tile(grid, 470, 14, FLOOR1)
    set_tile(grid, 471, 14, FLOOR1)
    set_tile(grid, 472, 14, FLOOR1)
    set_tile(grid, 473, 14, FLOOR1)
    ground_spike(470, 15)
    ground_spike(471, 15, v)

    # Final bouncer choice: bounce high over spike field or stay low
    set_bouncer(grid, 476, 15)
    # High floating path
    set_tile(grid, 479, 11, FLOOR1)
    set_tile(grid, 480, 11, FLOOR1)
    set_tile(grid, 481, 11, FLOOR1)
    set_tile(grid, 483, 11, FLOOR1)
    set_tile(grid, 484, 11, FLOOR1)
    # Low path with spikes
    ground_spike(479, 15)
    ground_spike(480, 15, v)
    ground_spike(483, 15)

    # Merge - safe ground
    # Half-platform decoration leading to end
    set_tile(grid, 488, 14, FLOOR1)
    set_tile(grid, 489, 14, FLOOR1)
    set_tile(grid, 490, 14, FLOOR1)

    set_tile(grid, 494, 13, FLOOR1)
    set_tile(grid, 495, 13, FLOOR1)

    # Decorative half-platforms near finish
    set_tile(grid, 500, 14, FLOOR1)
    set_tile(grid, 501, 14, FLOOR1)
    set_tile(grid, 503, 12, FLOOR1)
    set_tile(grid, 504, 12, FLOOR1)
    set_tile(grid, 506, 14, FLOOR1)
    set_tile(grid, 507, 14, FLOOR1)

    # === End portal (cols 510-511) ===
    # Last two lines are the rocket-ON portal (matching original)
    # Portal is 2 cols wide, 3 rows tall, placed at rows 14-16
    place_rocket_on(grid, 510, 14)

    return grid

def grid_to_asm(grid):
    lines = []
    lines.append("")
    lines.append('SECTION "leveldata2",ROMX[$4000],BANK[6]')
    lines.append("Level2:")
    lines.append("")

    for col in range(COLS):
        values = ", ".join(grid[col])
        lines.append(f"  db {values}, ")

    lines.append("  Level2End:")
    lines.append("")
    lines.append("")
    lines.append("DEF level2Height EQU $12")
    lines.append("DEF level2Width EQU ((LevelEnd-Level)/levelHeight)")
    lines.append("")

    return "\n".join(lines)

if __name__ == "__main__":
    grid = generate_level()
    asm = grid_to_asm(grid)
    with open("level2.asm", "w") as f:
        f.write(asm)
    print(f"Generated level2.asm with {COLS} columns")

    # Count non-empty columns
    non_empty = 0
    for col in range(COLS):
        has_content = False
        for row in range(PLAY_ROWS):
            if grid[col][row] != o:
                has_content = True
                break
        if has_content:
            non_empty += 1
    print(f"Columns with content: {non_empty}/{COLS}")
