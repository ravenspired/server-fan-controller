from machine import Pin, PWM, I2C
import ssd1306
import utime

# ===== CONFIG =====
PWM_PIN = 15
ENC_A_PIN = 16
ENC_B_PIN = 17
ENC_SW_PIN = 18
I2C_SCL = 5
I2C_SDA = 4
OLED_WIDTH = 128
OLED_HEIGHT = 64
INACTIVITY_TIMEOUT = 60  # seconds
# ==================

# ===== GLOBALS =====
fan_on = True
speed = 50          # Initial speed %
last_interaction = utime.time()

# ===== PWM SETUP =====
pwm = PWM(Pin(PWM_PIN))
pwm.freq(25000)

def set_pwm(duty_percent):
    global fan_on
    if not fan_on:
        duty_percent = 90
    duty_percent = min(max(duty_percent, 0), 100)
    pwm_val = int((100 - duty_percent) * 65535 // 100)
    pwm.duty_u16(pwm_val)

# ===== OLED SETUP =====
i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA))
oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

# ===== LARGE DIGIT DISPLAY =====
def draw_large_number(num):
    oled.fill(0)
    if not fan_on or speed >= 90:
        oled.text("OFF", 20, 20, 1)
    else:
        # Large font: two digits + %
        digits = str(num)
        x = 0
        for d in digits:
            oled.text(d, x, 10, 1)  # top-left positioning
            x += 60  # spacing between digits
        oled.text("%", x, 20, 1)
    oled.show()

def clear_display():
    oled.fill(0)
    oled.show()

# ===== ROTARY ENCODER =====
enc_a = Pin(ENC_A_PIN, Pin.IN, Pin.PULL_UP)
enc_b = Pin(ENC_B_PIN, Pin.IN, Pin.PULL_UP)
enc_sw = Pin(ENC_SW_PIN, Pin.IN, Pin.PULL_UP)
last_enc_a = enc_a.value()

def encoder_update(pin):
    global speed, last_interaction
    a = enc_a.value()
    b = enc_b.value()
    delta = 0
    if a != last_enc_a:
        if b != a:
            delta = 1
        else:
            delta = -1
        speed += delta
        speed = min(max(speed, 0), 100)
        last_interaction = utime.time()
        set_pwm(speed)
        draw_large_number(speed)
    global last_enc_a
    last_enc_a = a

enc_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_update)

# ===== BUTTON CLICK =====
def button_pressed(pin):
    global fan_on, last_interaction
    fan_on = not fan_on
    last_interaction = utime.time()
    set_pwm(speed)
    draw_large_number(speed)

enc_sw.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed)

# ===== MAIN LOOP =====
set_pwm(speed)
draw_large_number(speed)

while True:
    if utime.time() - last_interaction > INACTIVITY_TIMEOUT:
        clear_display()
    utime.sleep(0.1)
