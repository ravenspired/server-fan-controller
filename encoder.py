from machine import Pin
import time

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


