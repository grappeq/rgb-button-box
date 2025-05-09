from machine import Pin, PWM
import math, utime
try:
    import urandom as random      # saves RAM on MicroPython
except ImportError:
    import random                 # CPython / desktop testing

# ---------- CONFIG ----------
RGB_BUTTON_PINS = [
    { "red": 2, "green": 3, "blue": 4, "button": 5 },
    { "red": 6, "green": 7, "blue": 8, "button": 9 },
    { "red": 10, "green": 11, "blue": 12, "button": 13 },
]

BUTTON_LEFT_ID = 0
BUTTON_RIGHT_ID = 2
BUTTON_CENTER_ID = 1
# -----------------------------------------------

# --- init ---

# 9 PWM channels @ 1 kHz, 12‑bit
rgb_pwms = []
for rgb_button in RGB_BUTTON_PINS:
    pwm = {
        "red": PWM(Pin(rgb_button["red"], Pin.OUT), freq=1000, duty_u16=0),
        "green": PWM(Pin(rgb_button["green"], Pin.OUT), freq=1000, duty_u16=0),
        "blue": PWM(Pin(rgb_button["blue"], Pin.OUT), freq=1000, duty_u16=0),
    }
    rgb_pwms.append(pwm)

buttons = [Pin(b["button"], Pin.IN, Pin.PULL_UP) for b in RGB_BUTTON_PINS]

# --- helper functions ---

def set_rgb(idx, r, g, b):
    """0‑2, values 0‑65535"""
    rgb_pwms[idx]["red"].duty_u16(r)
    rgb_pwms[idx]["green"].duty_u16(g)
    rgb_pwms[idx]["blue"].duty_u16(b)


def cool_sequence(duration_ms=2000, steps=60):
    """
    Smooth rainbow sweep across the three RGB buttons.
    • duration_ms : total time for one cycle  (≈2 s default)
    • steps       : animation granularity    (higher = smoother)
    Returns a list [(r,g,b), (r,g,b), (r,g,b)] with the final colour
    for buttons 0, 1, 2 (LEFT, CENTRE, RIGHT).
    """
    delay = duration_ms // steps          # integer delay per frame
    start_phase = random.random() * 2*math.pi   # random 0-2π

    last_rgb = [(0,0,0)]*3                # will hold final state

    for i in range(steps + 1):            # +1 → seamless loop
        cycle_pos = (i / steps) * 2*math.pi   # 0 → 2π

        for idx in range(3):              # three buttons
            phase = start_phase + idx * 2*math.pi/3 + cycle_pos

            r = int((math.sin(phase)               * 0.5 + 0.5) * 65535)
            g = int((math.sin(phase + 2*math.pi/3) * 0.5 + 0.5) * 65535)
            b = int((math.sin(phase + 4*math.pi/3) * 0.5 + 0.5) * 65535)

            set_rgb(idx, r, g, b)

            if i == steps:                # remember final colour
                last_rgb[idx] = (r, g, b)

        utime.sleep_ms(delay)

    return last_rgb


# --- startup ---
cool_sequence(3000)


# --- main loop ---
palette = cool_sequence(3000) + [(0,0,0)]
state = [0,1,2]
while True:
    for i, btn in enumerate(buttons):
        if not btn.value():                 # pushed?
            state[i] = (state[i] + 1) % len(palette)
            set_rgb(i, *palette[state[i]])
            utime.sleep_ms(1000)            # crude debounce
    utime.sleep_ms(10)