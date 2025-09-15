from machine import Pin
import time

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

btn = Button(14)


