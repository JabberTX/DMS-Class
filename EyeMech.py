# Modified code from Will Cogley's original Eye Mech control code
# Updated to include auto/manual mode switching, squint toggle, and blinking.

# Requires the micropython-servo library
# https://pypi.org/project/micropython-servo/

# --- Import setup ---
import time
import random
from machine import Pin, ADC
from servo import Servo

# --- Hardware Setup ---
led = Pin(25, Pin.OUT) # Onboard LED
joy_button = Pin(22, Pin.IN, Pin.PULL_UP)  # Pin for mode/squint/blink button
# Joystick ADC pins
UD = ADC(26) # vertical
LR = ADC(27) # horizontal

# --- Eye servos --- 
servos = {
    "LR": Servo(pin_id=10),
    "UD": Servo(pin_id=11),
    "TL": Servo(pin_id=12),
    "BL": Servo(pin_id=13),
    "TR": Servo(pin_id=14),
    "BR": Servo(pin_id=15),
}

# --- Eye servo limits ---
servo_limits = {
    "LR": (55, 130),   
    "UD": (50, 140),
    "TL": (80, 170), 
    "BL": (90, 20),
    "TR": (90, 20),
    "BR": (90, 170),
}

# --- other variables ---
manual_mode = True
last_button_state = 1
press_time = 0
release_time = 0
click_count = 0
last_click_event = 0
next_auto_move = 0 
last_blink_time = 0
squiting = False 
long_press_handled = False

LONG_PRESS_THRESHOLD = 500 
DOUBLE_CLICK_GAP = 250  
DEBOUNCE = 50           

# --- Core Functions ---

# --- Blinking Function ---
def blink():
    lids = ["TL", "BL", "TR", "BR"]
    for name in lids:
        min_angle = servo_limits[name][0]
        servos[name].write(min_angle)

# --- Neutral Pose ---
def neutral():
    global squiting
    squiting = False
    servos["LR"].write(90)
    control_ud_and_lids(90)

#--- Vertical motion and eyelids ---
def control_ud_and_lids(ud_angle):
    ud_min, ud_max = servo_limits["UD"]
    ud_progress = (ud_angle - ud_min) / (ud_max - ud_min)
    
    if squiting:
        tl_min, tl_max = 80, 110 
        tr_min, tr_max = 90, 60
        bl_min, bl_max = 90, 60
        br_min, br_max = 90, 120
    else:
        tl_min, tl_max = servo_limits["TL"]
        tr_min, tr_max = servo_limits["TR"]
        bl_min, bl_max = servo_limits["BL"]
        br_min, br_max = servo_limits["BR"]

    # Calculate eyelid positions based on UD position
    tl_target = tl_max - ((tl_max - tl_min)*(0.8*(1-ud_progress)))
    tr_target = tr_max + ((tr_min - tr_max)*(0.8*(1-ud_progress)))
    bl_target = bl_max + ((bl_min - bl_max)*(0.4*(ud_progress)))
    br_target = br_max - ((br_max - br_min)*(0.4*(ud_progress)))
   
    # Move the servos
    servos["UD"].write(ud_angle)
    servos["TL"].write(tl_target)
    servos["TR"].write(tr_target)
    servos["BL"].write(bl_target)
    servos["BR"].write(br_target)

# --- Scaling Function ---
def scale_potentiometer(pot_value, servo, reverse=False):
    in_min, in_max = 300, 65300
    min_limit, max_limit = servo_limits[servo]
    scaled_value = min_limit + (pot_value - in_min) * (max_limit - min_limit) / (in_max - in_min)
    if reverse:
        scaled_value = max_limit - (scaled_value - min_limit)
    return scaled_value

# --- Main Loop ---
while True:
    now = time.ticks_ms()
    is_pressed = (joy_button.value() == 0)
    
    # Button Logic
    if is_pressed and last_button_state == 1:
        if (now - release_time) > DEBOUNCE:
            press_time = now
            last_button_state = 0
            long_press_handled = False
            
    if not is_pressed and last_button_state == 0:
        hold_time = now - press_time
        if not long_press_handled and hold_time > DEBOUNCE:
            click_count += 1
            last_click_event = now
        last_button_state = 1
        release_time = now

    # Long Press Handler
    if is_pressed and not long_press_handled and (now - press_time) > LONG_PRESS_THRESHOLD:
        squiting = not squiting
        long_press_handled = True
        print("Squint:", "ON" if squiting else "OFF")

    # Process Clicks
    if click_count > 0 and (now - last_click_event) > DOUBLE_CLICK_GAP:
        # Double Click / Mode Switch
        if click_count >= 2:
            manual_mode = not manual_mode
            if not manual_mode: neutral()
            print("Mode:", "MANUAL" if manual_mode else "AUTO")
        # Single Click / Blink
        elif click_count == 1 and manual_mode:
            blink()
            print("Blink")
            last_blink_time = now
        click_count = 0

    # Manual mode / Auto mode
    if manual_mode:
        led.on()
        if (now - last_blink_time) > 200: 
            lr_angle = scale_potentiometer(LR.read_u16(), "LR", reverse=True)
            ud_angle = scale_potentiometer(UD.read_u16(), "UD")
            servos["LR"].write(lr_angle)
            control_ud_and_lids(ud_angle)
    else:
        led.off()
        if now > next_auto_move:
            command = random.randint(0, 2)
            if command == 0: 
                blink()
                next_auto_move = now + 250
            elif command == 1:
                blink()
                control_ud_and_lids(random.randint(servo_limits["UD"][0], servo_limits["UD"][1]))
                servos["LR"].write(random.randint(servo_limits["LR"][0], servo_limits["LR"][1]))
                next_auto_move = now + random.randint(500, 1200)
            else:
                control_ud_and_lids(random.randint(servo_limits["UD"][0], servo_limits["UD"][1]))
                servos["LR"].write(random.randint(servo_limits["LR"][0], servo_limits["LR"][1]))
                next_auto_move = now + random.randint(300, 800)
             
    time.sleep_ms(10)
    
