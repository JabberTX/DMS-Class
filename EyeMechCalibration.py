import time
from machine import Pin, ADC
from servo import Servo

# --- Hardware ---
joy_button = Pin(22, Pin.IN, Pin.PULL_UP)
UD = ADC(26)
LR = ADC(27)

servos = {
    "LR": Servo(pin_id=10),
    "UD": Servo(pin_id=11),
    "TL": Servo(pin_id=12),
    "BL": Servo(pin_id=13),
    "TR": Servo(pin_id=14),
    "BR": Servo(pin_id=15),
}

# --- State Management ---
# 0 = Eyes (LR/UD), 1 = Left Lids, 2 = Right Lids
current_mode = 0 
mode_names = ["EYE MOVEMENT", "LEFT EYELIDS", "RIGHT EYELIDS"]

# --- Helper: Scaling ---
def get_joystick_angle(adc_obj, reverse=False):
    val = adc_obj.read_u16()
    angle = int(0 + (val - 300) * (180 - 0) / (65300 - 300))
    return (180 - angle) if reverse else angle

# --- Main Loop ---
print("System Ready. Mode: EYE MOVEMENT")

while True:
    button_val = joy_button.value()
    is_pressed = (button_val == 0)

    if joy_button.is_pressed:
        current_mode = (current_mode + 1) % 3
        print(f"\n--- SWITCHED TO: {mode_names[current_mode]} ---")
        time.sleep(0.5)
    
    h_angle = get_joystick_angle(LR, reverse=True)
    v_angle = get_joystick_angle(UD)
    
    if current_mode == 0:
        # Control Eyeballs
        servos["LR"].write(h_angle)
        servos["UD"].write(v_angle)
        print(f"EYES -> LR: {h_angle} | UD: {v_angle}    ", end="\r")

    elif current_mode == 1:
        # Control Left Eyelids
        servos["TL"].write(h_angle)
        servos["BL"].write(v_angle)
        print(f"LEFT LIDS -> TL: {h_angle} | BL: {v_angle}    ", end="\r")

    elif current_mode == 2:
        # Control Right Eyelids
        servos["TR"].write(h_angle)
        servos["BR"].write(v_angle)
        print(f"RIGHT LIDS -> TR: {h_angle} | BR: {v_angle}    ", end="\r")

    time.sleep_ms(50)
    
