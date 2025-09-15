# main.py - PWM fan control with rotary encoder + SSD1306 OLED (MicroPython)
# Pins used (change if you need):
# I2C: GP0 = SDA, GP1 = SCL
# Rotary encoder: A=GP2, B=GP3
# Encoder push button: GP14 (Button class uses 14 by default below)
# PWM fan pin: GP15 (change pwm_pin if you'd like different pin)
# OLED address: 0x3C (common)

from machine import Pin, I2C, PWM
import time
from micropython import const
import framebuf

# -------------------------
# SSD1306 driver (as provided)
# -------------------------
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)

class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,  # off
            SET_MEM_ADDR,
            0x00,  # horizontal
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01,
            SET_MUX_RATIO,
            self.height - 1,
            SET_COM_OUT_DIR | 0x08,
            SET_DISP_OFFSET,
            0x00,
            SET_COM_PIN_CFG,
            0x02 if self.width > 2 * self.height else 0x12,
            SET_DISP_CLK_DIV,
            0x80,
            SET_PRECHARGE,
            0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL,
            0x30,
            SET_CONTRAST,
            0xFF,
            SET_ENTIRE_ON,
            SET_NORM_INV,
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        # writevto exists on many MicroPython ports for performance; if not, fallback:
        try:
            self.i2c.writevto(self.addr, self.write_list)
        except AttributeError:
            # fallback: send in 16KB chunks
            self.i2c.writeto(self.addr, b"\x40" + buf)


# -------------------------
# Button class (as provided)
# -------------------------
class Button:
    def __init__(self, pin_number, check_enabled=True, debounce_ms=50):
        self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
        self.check_enabled = check_enabled
        self._last_state = self.pin.value()
        self._last_time = time.ticks_ms()
        self._debounce_ms = debounce_ms
        self.is_pressed = False  # True only on the press event

    def update(self):
        if not self.check_enabled:
            self.is_pressed = False
            return

        current_state = self.pin.value()
        now = time.ticks_ms()

        if current_state != self._last_state:
            # Only react after stable debounce period
            if time.ticks_diff(now, self._last_time) > self._debounce_ms:
                self._last_time = now
                if current_state == 0 and self._last_state == 1:
                    self.is_pressed = True  # Button was just pressed
                else:
                    self.is_pressed = False
            else:
                self.is_pressed = False
        else:
            self.is_pressed = False

        self._last_state = current_state

    def enable(self):
        self.check_enabled = True

    def disable(self):
        self.check_enabled = False
        self.is_pressed = False

# default button instance on GP14 (matches your provided snippet)
btn = Button(14)


# -------------------------
# Rotary encoder class (as provided)
# -------------------------
class RotaryEncoder:
    def __init__(self, pin_a, pin_b, debounce_us=1000):
        self.pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self.step_position = 0
        self.debounce_us = debounce_us
        self.last_time = time.ticks_us()

        self.state = (self.pin_a.value() << 1) | self.pin_b.value()
        self.prev_state = self.state
        self.seq = []

        self.valid_steps = [
            [0, 1, 3, 2],  # CW sequence
            [0, 2, 3, 1]   # CCW sequence
        ]

        self.pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._update)
        self.pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._update)

    def _update(self, pin):
        now = time.ticks_us()
        if time.ticks_diff(now, self.last_time) < self.debounce_us:
            return

        new_state = (self.pin_a.value() << 1) | self.pin_b.value()
        if new_state != self.prev_state:
            self.seq.append(new_state)
            if len(self.seq) > 4:
                self.seq.pop(0)

            if self.seq == self.valid_steps[0]:  # Clockwise
                self.step_position += 1
                self.seq.clear()
            elif self.seq == self.valid_steps[1]:  # Counter-clockwise
                self.step_position -= 1
                self.seq.clear()

            self.prev_state = new_state
            self.last_time = now

    def get_position(self):
        return self.step_position

    def reset(self):
        self.step_position = 0
        self.seq = []

# -------------------------
# Big font (5x7) for digits, % sign, and letters O F
# We'll use a small built-in 5x7-style map (bitmaps)
# Each glyph is 5 columns wide, 7 rows high (LSB = top pixel)
# -------------------------
FONT_5x7 = {
    '0': [0x3E,0x45,0x49,0x51,0x3E],  # 0
    '1': [0x00,0x21,0x7F,0x01,0x00],  # 1
    '2': [0x23,0x45,0x49,0x49,0x31],  # 2
    '3': [0x22,0x41,0x49,0x49,0x36],  # 3
    '4': [0x0C,0x14,0x24,0x7F,0x04],  # 4
    '5': [0x72,0x51,0x51,0x51,0x4E],  # 5
    '6': [0x3E,0x49,0x49,0x49,0x26],  # 6
    '7': [0x40,0x47,0x48,0x50,0x60],  # 7
    '8': [0x36,0x49,0x49,0x49,0x36],  # 8
    '9': [0x32,0x49,0x49,0x49,0x3E],  # 9
    '%': [0x63,0x64,0x08,0x13,0x63],  # %
    'O': [0x3E,0x41,0x41,0x41,0x3E],  # O
    'F': [0x7F,0x48,0x48,0x48,0x40],  # F
    ' ': [0x00,0x00,0x00,0x00,0x00],  # space
    '-': [0x08,0x08,0x08,0x08,0x08],  # dash
}



# -------------------------
# Helper: draw big text using 5x7 glyphs scaled by integer scale
# -------------------------
def draw_big_text(oled, text, scale=4):
    oled.fill(0)
    # compute width of entire text
    char_w = 5
    spacing = 1
    total_w = len(text) * (char_w + spacing) * scale
    # center horizontally and vertically
    x = max((oled.width - total_w) // 2, 0)
    y = max((oled.height - (7 * scale)) // 2, 0)
    for ch in text:
        glyph = FONT_5x7.get(ch, FONT_5x7[' '])
        # each column in glyph is a byte (we'll use lower 7 bits)
        for col in range(char_w):
            col_byte = glyph[col]
            for sy in range(7):
                pixel_on = (col_byte >> (6 - sy)) & 1  # top bit first
                if pixel_on:
                    # draw scaled vertical column of pixels at (x + col*scale, y + sy*scale)
                    px = x + col * scale
                    py = y + sy * scale
                    for dx in range(scale):
                        for dy in range(scale):
                            oled.pixel(px + dx, py + dy, 1)
        x += (char_w + spacing) * scale
    oled.show()

# -------------------------
# Mapping percent -> duty (inverted)
# percent in [25..75] maps to duty_u16 [65535 .. 0], 90% -> OFF (0)
# -------------------------
def percent_to_duty_u16(p):
    """
    Map 0..100% input to 25..75% inverted PWM duty.
    0% -> 75% duty (slow)
    100% -> 25% duty (fast)
    """
    # clamp input
    p = max(0, min(100, p))
    
    # map 0..100 -> 75..25 linearly
    duty_percent = 75 - (p * 50 // 100)  # integer percent
    
    # convert percent to u16 duty (0..65535)
    duty_u16 = int(duty_percent / 100 * 65535)
    return duty_u16


def display_percent(p):
    if p >= 90:
        return 0  # OFF
    # map 25..75 -> 100..0
    return int((75 - p) * 2)

# -------------------------
# Setup hardware (pins)
# -------------------------
# change pins here if needed
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)

encoder = RotaryEncoder(12, 13)
# btn instance already created above using GP14

pwm_pin_num = 15
pwm_pin = Pin(pwm_pin_num, Pin.OUT)
pwm = PWM(pwm_pin)
pwm.freq(25000)  # typical for brushless fans (25 kHz). Adjust if needed.

# -------------------------
# Variables / state
# -------------------------
MIN_P = 25
MAX_P = 75
DEFAULT_P = 25

current_percent = DEFAULT_P  # user-set percent (25..75)
saved_percent = current_percent  # used when toggling OFF/ON
display_on = True
last_input_ms = time.ticks_ms()
DISPLAY_TIMEOUT_MS = 60_000  # 1 minute

# initial apply
pwm.duty_u16(percent_to_duty_u16(current_percent))
draw_big_text(oled, "{:d}%".format(display_percent(current_percent)), scale=4)


# -------------------------
# Main loop
# -------------------------
def clamp(v, a, b):
    return max(a, min(b, v))

# read encoder periodically; we'll poll step_position every 50ms
while True:
    now = time.ticks_ms()

    # read encoder steps
    steps = encoder.get_position()
    if steps != 0:
        # adjust percent: 1 step -> 1 percent change
        current_percent = int(current_percent + steps)
        current_percent = clamp(current_percent, MIN_P, MAX_P)
        # when rotating while OFF (90%), update saved_percent not visible until toggled on
        if current_percent != 90:
            saved_percent = current_percent
        # apply to PWM if not OFF
        pwm.duty_u16(percent_to_duty_u16(current_percent))
        encoder.reset()
        last_input_ms = now
        # ensure display is on
        if not display_on:
            oled.poweron()
            display_on = True
        # redraw
        draw_big_text(oled, "{:d}%".format(display_percent(current_percent)), scale=4)


    print(current_percent)

    # update button (push)
    btn.update()
    if btn.is_pressed:
        # toggle: if currently not OFF -> set to OFF (90) and save prior
        if current_percent < 90:
            saved_percent = current_percent
            current_percent = 90
            pwm.duty_u16(percent_to_duty_u16(current_percent))  # becomes 0
            # ensure display on and show OFF
            if not display_on:
                oled.poweron()
                display_on = True
            draw_big_text(oled, "OFF", scale=4)
        else:
            # currently OFF -> restore saved
            current_percent = clamp(saved_percent, MIN_P, MAX_P)
            pwm.duty_u16(percent_to_duty_u16(current_percent))
            if not display_on:
                oled.poweron()
                display_on = True
            draw_big_text(oled, "{:d}%".format(display_percent(current_percent)), scale=4)
        last_input_ms = now

    # handle OLED timeout (turn off display after inactivity)
    if display_on and time.ticks_diff(now, last_input_ms) > DISPLAY_TIMEOUT_MS:
        oled.poweroff()
        display_on = False

    # small sleep to reduce CPU usage
    time.sleep_ms(40)
