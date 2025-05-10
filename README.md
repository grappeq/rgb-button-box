# 🎨 RGB Button Box toy
> Three buttons, one hue, endless toddler triumphs.
![A cool GIF](/docs/showcase.gif)

## What’s in the repo?
* `main.py` — MicroPython script that makes LEDs sparkle and tiny humans giggle.  
* `designs/circuit` — Simple RP2040-style wiring: 3 × RGB LEDs + 3 × momentary push-buttons (share the PCB with polite firmware).  
* `designs/3d` — A slick enclosure that looks like a designer speaker but is, in fact, a baby’s first puzzle cube.

## The Game
1. Mash any button.  
2. Each thump steps that button through a pre-baked rainbow.  
3. Get all three buttons to glow **the same colour**.  
4. Bask in victory flashes, then watch the palette reshuffle itself faster than you can say “again!”

## Building your own

### Parts needed
* 3x RGB buttons
* 1x bistable switch (on/off power)
* 9x 470 Ohm resistors
* 1x Raspberry Pi Pico
* 5x M3 brass heated inserts (will need to be pressed into 4.5mm holes)
* Few M3 screws to put it all together
* 2x M2 screws to hold the power switch
* 3d-printed case (designs are in the repo [here](/designs/3d/))


### Wiring everything together
![Circuit](/designs/circuit/Button%20box_schem.png)

### Code
1. Flash MicroPython on your RP2040 board
2. Drop `main.py` onto the device
3. Power up → admire the startup light show

## Custom Tweaks
Open `main.py` and twiddle:
* `GAMMA` — sweet-spot brightness curve.
* `RGB_BUTTON_PINS` — pinout if you didn’t follow my PCB.
* `rainbow()` timings — from chill aurora to disco strobe.

## License
MIT. Hack it, print it, gift it.

Happy hacking! 🚀
