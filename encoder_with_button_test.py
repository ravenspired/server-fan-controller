from button import Button
from encoder import RotaryEncoder
import time

encoder = RotaryEncoder(12, 13)

enter_btn = Button(15)
back_btn = Button(14)

while True:
    enter_btn.update()
    back_btn.update()
    position = encoder.get_position()
    
    # Ensure the position is printed continuously
    print("Current position:", position)
    
    if enter_btn.is_pressed:
        print("Button was pressed!")
    if back_btn.is_pressed:
        print("Back button was pressed!")
    time.sleep(0.1)  # Small delay for readability



