# ─── imports ───────────────────────────────────────────────────────────
import math, random
import uasyncio as asyncio          # <── async event-loop
from machine import Pin, PWM

# ─── CONFIGURATION ─────────────────────────────────────────────────────
RGB_BUTTON_PINS = [
    {"red": 2,  "green": 3,  "blue": 4,  "button": 5},
    {"red": 6,  "green": 7,  "blue": 8,  "button": 9},
    {"red": 10, "green": 11, "blue": 12, "button": 13},
]

# ─── initialisation ────────────────────────────────────────────────────
rgb_pwms = []
for spec in RGB_BUTTON_PINS:
    rgb_pwms.append({
        "red"  : PWM(Pin(spec["red" ],  Pin.OUT), freq=1_000, duty_u16=0),
        "green": PWM(Pin(spec["green"], Pin.OUT), freq=1_000, duty_u16=0),
        "blue" : PWM(Pin(spec["blue"],  Pin.OUT), freq=1_000, duty_u16=0),
    })

buttons  = [Pin(spec["button"], Pin.IN, Pin.PULL_UP) for spec in RGB_BUTTON_PINS]
states   = [0, 1, 2]                         # which colour‐index each button is on
PALETTE  = []                                # filled in by the rainbow task

# ─── helper: set one RGB LED ───────────────────────────────────────────
def set_rgb(idx, r, g, b):
    rgb_pwms[idx]["red"  ].duty_u16(r)
    rgb_pwms[idx]["green"].duty_u16(g)
    rgb_pwms[idx]["blue" ].duty_u16(b)

# ─── async rainbow animator ────────────────────────────────────────────
async def cool_sequence(duration_ms=2_000, steps=60):
    """
    Drives all three LEDs through a rainbow and updates the global
    PALETTE with the colours that the sequence ends on.
    Yields every frame so other tasks can run.
    """
    global PALETTE
    delay      = duration_ms // steps
    start_phi  = random.random() * 2*math.pi
    last_rgb   = [(0,0,0)] * 3

    for i in range(steps + 1):              # +1 → seamless loop
        theta = i / steps * 2*math.pi       # 0 → 2π
        for idx in range(3):
            phi = start_phi + idx * 2*math.pi/3 + theta
            r = int((math.sin(phi)               * 0.5 + 0.5) * 65535)
            g = int((math.sin(phi + 2*math.pi/3) * 0.5 + 0.5) * 65535)
            b = int((math.sin(phi + 4*math.pi/3) * 0.5 + 0.5) * 65535)
            set_rgb(idx, r, g, b)
            if i == steps:
                last_rgb[idx] = (r, g, b)
        await asyncio.sleep_ms(delay)       # <-- yields to event-loop

    PALETTE = last_rgb + [(0,0,0)]          # last three + “off”

# ─── async button handler (one per button) ─────────────────────────────
async def watch_button(idx):
    pin = buttons[idx]
    global states
    while True:
        if not pin.value():                 # active-low pressed?
            states[idx] = (states[idx] + 1) % len(PALETTE)
            set_rgb(idx, *PALETTE[states[idx]])
            # simple async debounce: wait until released & 40 ms extra
            while not pin.value():
                await asyncio.sleep_ms(10)
            await asyncio.sleep_ms(40)
        await asyncio.sleep_ms(10)          # poll interval

# ─── main task spawner ─────────────────────────────────────────────────
async def main():
    # kick off the rainbow loop for ever
    asyncio.create_task(cool_sequence(3000))
    # individual button watchers
    for idx in range(3):
        asyncio.create_task(watch_button(idx))

    # the event-loop needs at least one pending awaitable:
    while True:
        await asyncio.sleep(3600)           # sleep “forever”

# ─── run it ────────────────────────────────────────────────────────────
asyncio.run(main())
