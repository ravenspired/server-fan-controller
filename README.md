# server-fan-controller

A MicroPython-based PWM fan controller for Raspberry Pi Pico (or similar), featuring a rotary encoder for speed adjustment and an SSD1306 OLED display for real-time feedback.

## Features

- **PWM Fan Control:** Adjusts fan speed via PWM on a configurable GPIO pin.
- **Rotary Encoder Input:** Use a rotary encoder to set the fan speed (1–100%).
- **OLED Display:** SSD1306 128x64 I2C OLED shows current speed or OFF state in large digits.
- **Push Button:** Encoder button toggles the fan ON/OFF.
- **Auto Display Off:** OLED powers down after 1 minute of inactivity to save energy.
- **Debounced Inputs:** Reliable handling of encoder and button events.

## Hardware Connections

| Function           | Pico Pin | Default |
|--------------------|----------|---------|
| I2C SDA (OLED)     | GP0      | 0       |
| I2C SCL (OLED)     | GP1      | 1       |
| Encoder A          | GP2      | 12      |
| Encoder B          | GP3      | 13      |
| Encoder Button     | GP14     | 14      |
| PWM Fan Output     | GP15     | 15      |

- **OLED I2C Address:** `0x3C` (common default)
- **PWM Frequency:** 25 kHz (adjustable)

## Usage

1. **Wire up** the hardware as per the table above.
2. **Copy `main.py`** to your MicroPython device.
3. **Power on** the device.
4. **Turn the encoder** to set fan speed (1–100%).
5. **Press the encoder button** to toggle the fan ON/OFF.
6. **OLED display** will show the current speed or "OFF".

## Customization

- Change pin assignments at the top of `main.py` if needed.
- Adjust `DISPLAY_TIMEOUT_MS` for OLED timeout duration.
- Modify `MIN_P`/`MAX_P` for allowed speed range.

## Example

![OLED showing 45%](docs/example-oled.jpg)

## Dependencies

- MicroPython firmware for Raspberry Pi Pico (or compatible)
- SSD1306 OLED display (I2C)
- Rotary encoder with push button
- 4-wire PWM fan

## License

MIT License

