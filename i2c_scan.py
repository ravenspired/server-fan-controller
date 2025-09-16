from machine import Pin, I2C
i2c = I2C(0, scl=Pin(1), sda=Pin(0))  # adjust pins if different
print(i2c.scan())
