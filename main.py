# ── imports ────────────────────────────────────────────────────────────
import math, random
import uasyncio as asyncio
from machine import Pin, PWM

# ── config ─────────────────────────────────────────────────────────────
RGB_BUTTON_PINS = [
    {"red": 2,  "green": 3,  "blue": 4,  "button": 5},
    {"red": 6,  "green": 7,  "blue": 8,  "button": 9},
    {"red": 10, "green": 11, "blue": 12, "button": 13},
]

# ── hardware init ──────────────────────────────────────────────────────
rgb_pwms = []
for spec in RGB_BUTTON_PINS:
    rgb_pwms.append({
        "red"  : PWM(Pin(spec["red" ],  Pin.OUT), freq=1_000, duty_u16=0),
        "green": PWM(Pin(spec["green"], Pin.OUT), freq=1_000, duty_u16=0),
        "blue" : PWM(Pin(spec["blue"],  Pin.OUT), freq=1_000, duty_u16=0),
    })

buttons = [Pin(spec["button"], Pin.IN, Pin.PULL_UP) for spec in RGB_BUTTON_PINS]

# ── globals used by the coroutines ─────────────────────────────────────
PALETTE     = []            # [(r,g,b), … , (0,0,0)]  length ≥ 4
states      = [0, 1, 2]     # current palette index of each button
sync_event  = asyncio.Event()   # set when all three indices equal

# ── helpers ────────────────────────────────────────────────────────────
def set_rgb(idx, r, g, b):
    rgb_pwms[idx]["red"  ].duty_u16(r)
    rgb_pwms[idx]["green"].duty_u16(g)
    rgb_pwms[idx]["blue" ].duty_u16(b)

def all_equal(lst):
    return lst[1:] == lst[:-1]

# ── async rainbow sweep (finite-length) ────────────────────────────────
async def rainbow(duration_ms=3000, steps=60, loops=1):
    """
    Run `loops` complete rainbow cycles.

    • duration_ms : time for ONE cycle (not total)  
    • steps       : frames per cycle (≥12 looks smooth on RP2040)  
    • loops       : how many cycles to do before returning

    On exit PALETTE is set to the colours from the LAST cycle.
    """
    global PALETTE
    start_phi = random.random() * 2*math.pi

    for loop in range(loops):
        last_rgb   = [(0,0,0)]*3
        for i in range(steps + 1):                 # +1 gives perfect wrap
            theta = i / steps * 2*math.pi          # 0 → 2π
            for idx in range(3):
                phi = start_phi + idx*2*math.pi/3 + theta
                r = int((math.sin(phi)               * .5 + .5) * 65535)
                g = int((math.sin(phi + 2*math.pi/3) * .5 + .5) * 65535)
                b = int((math.sin(phi + 4*math.pi/3) * .5 + .5) * 65535)
                set_rgb(idx, r, g, b)
                if i == steps:
                    last_rgb[idx] = (r, g, b)
            # -- make it as quick as the MCU allows, but never sleep <1 ms
            delay = max(1, duration_ms // steps)
            await asyncio.sleep_ms(delay)

        # rainbows are additive, so vary the start angle each loop
        start_phi += random.random() * 2*math.pi

    PALETTE = last_rgb + [(0,0,0)]
    return PALETTE

# ---------------------------------------------------------------
#  Startup: all LEDs off → FADE LED-0 → FADE LED-1 → FADE LED-2
#           → one rainbow cycle → normal operation
# ---------------------------------------------------------------
async def startup_sequence(
        pre_colour=(40000, 40000, 40000),  # target “white” for fade
        fade_ms=400,                      # how long the fade for ONE LED lasts
        steps=32,                         # more steps = smoother fade
        gap_ms=120):                      # pause after each LED reaches full
    """
    Power-on flourish with per-LED fades (non-blocking).

    • All LEDs off
    • Each LED ramps from 0 → pre_colour in `fade_ms`
    • Little gap, then next LED
    • Finishes with one rainbow() to build the new palette
    """

    # 0) lights off
    for idx in range(3):
        set_rgb(idx, 0, 0, 0)
    await asyncio.sleep_ms(gap_ms)

    # 1) sequential fade-in
    step_delay = max(1, fade_ms // steps)
    for idx in range(3):
        for n in range(steps + 1):                # 0 … steps
            f = n / steps                         # 0.0 → 1.0
            r = int(pre_colour[0] * f)
            g = int(pre_colour[1] * f)
            b = int(pre_colour[2] * f)
            set_rgb(idx, r, g, b)
            await asyncio.sleep_ms(step_delay)
        await asyncio.sleep_ms(gap_ms)

    # 2) run a rainbow once (adjust speed to taste)
    await rainbow(duration_ms=400, steps=24, loops=3)


# ── async flash sequence ───────────────────────────────────────────────
async def flash(times=3, on_ms=120, off_ms=120):
    current = PALETTE[states[0]]       # all three are the same colour
    for _ in range(times):
        for idx in range(3):
            set_rgb(idx, *current)
        await asyncio.sleep_ms(on_ms)
        for idx in range(3):
            set_rgb(idx, 0, 0, 0)
        await asyncio.sleep_ms(off_ms)
    # leave LEDs off until next rainbow starts

# ── button watcher (one per button) ────────────────────────────────────
async def watch_button(idx):
    pin = buttons[idx]
    global states
    while True:
        if not pin.value():                        # pressed?
            states[idx] = (states[idx] + 1) % len(PALETTE)
            set_rgb(idx, *PALETTE[states[idx]])

            # async debounce
            while not pin.value():
                await asyncio.sleep_ms(10)
            await asyncio.sleep_ms(40)

            # did this press make them all the same?
            if all_equal(states):
                sync_event.set()

        await asyncio.sleep_ms(10)

# ── orchestrator: reacts to “all-three-match” ─────────────────────────
async def sync_manager():
    global states
    while True:
        await sync_event.wait()       # waits until set by watcher
        sync_event.clear()

        await flash()                 # flash a few times
        # flash ➔ run 3 ultra-fast rainbows (0.4 s each)
        await rainbow(duration_ms=400, steps=24, loops=3)

        # 3) re-seed button indices so LEDs differ again
        states[:] = [0, 1, 2]
        for idx in range(3):
            set_rgb(idx, *PALETTE[states[idx]])

# ── main entry point ───────────────────────────────────────────────────
async def main():
    await startup_sequence()                  # initial palette
    for idx in range(3):
        asyncio.create_task(watch_button(idx))
    asyncio.create_task(sync_manager())

    # keep the loop alive
    while True:
        await asyncio.sleep(3600)

# ── run it ─────────────────────────────────────────────────────────────
asyncio.run(main())
