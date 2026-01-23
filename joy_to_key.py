import pygame
from pynput.keyboard import Controller, Key
import time
import json

config_json = None
keyboard_map_json = None

with open("config.json", "r", encoding="utf-8") as file:
    config_json = json.load(file)
with open("keyboard_map.json", "r", encoding="utf-8") as file:
    keyboard_map_json = json.load(file)


# Initialize keyboard controller
keyboard = Controller()

# Initialize pygame joystick
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    raise RuntimeError("No joystick detected")

js = pygame.joystick.Joystick(0)
js.init()

print(f"Joystick detected: {js.get_name()}")

# Deadzone to avoid drift
DEADZONE = 0.1

def press(key):
    keyboard.press(key)

def release(key):
    keyboard.release(key)

def get_val(dict_input, *args):
    val = None
    # print(f'args: {args}')
    for arg in args:
        val = dict_input.get(arg, None)

        # print(val, type(val))
        if isinstance(val, dict):
            dict_input = val
        else:
            break
    
    return val

def eval_key(*args):
    config_key = get_val(config_json, *args)

    if config_key is not None:
        map_key = get_val(keyboard_map_json, *args)
        if map_key is not None and map_key != 'None':
            if js.get_button(config_key):
                try:
                    press(Key.__dict__[map_key])
                except KeyError:
                    press(map_key)
            else:
                try:
                    release(Key.__dict__[map_key])
                except KeyError:
                    release(map_key)

if __name__ == "__main__":
    x_hat_timeout = 0.01
    y_hat_timeout = 0.01
    x_hat_start = time.monotonic()
    y_hat_start = time.monotonic()

    try:
        while True:
            pygame.event.pump()

            # Read axes (commonly: 0 = X, 1 = Y)
            x = js.get_axis(config_json["axes"]["left_stick"]["left_right"])
            y = js.get_axis(config_json["axes"]["left_stick"]["up_down"]) or js.get_axis(config_json["axes"]["right_stick"]["up_down"])


            # Dpad
            x_hat = js.get_hat(0)[config_json["hats"]["left_right"]]
            y_hat = (-1 *(js.get_hat(0)[config_json["hats"]["up_down"]]))

            if x_hat:
                if time.monotonic() - x_hat_start > x_hat_timeout:
                    x = x or x_hat
                    x_hat_timeout = 0.15
                    x_hat_start = time.monotonic()
            else:
                x_hat_timeout = 0.01
            if y_hat:
                if time.monotonic() - y_hat_start > y_hat_timeout:
                    y = y or y_hat
                    y_hat_timeout = 0.15
                    y_hat_start = time.monotonic()
            else:
                y_hat_timeout = 0.01


            # Horizontal movement
            if x < -DEADZONE:
                press(Key.__dict__[keyboard_map_json["axes"]["left_stick"]["left"]])
            else:
                release(Key.__dict__[keyboard_map_json["axes"]["left_stick"]["left"]])

            if x > DEADZONE:
                press(Key.__dict__[keyboard_map_json["axes"]["left_stick"]["right"]])
            else:
                release(Key.__dict__[keyboard_map_json["axes"]["left_stick"]["right"]])

            # Vertical movement
            if y < -DEADZONE:
                press(Key.__dict__[keyboard_map_json["axes"]["left_stick"]["up"]])
            else:
                release(Key.__dict__[keyboard_map_json["axes"]["left_stick"]["up"]])

            if y > DEADZONE:
                press(Key.__dict__[keyboard_map_json["axes"]["left_stick"]["down"]])
            else:
                release(Key.__dict__[keyboard_map_json["axes"]["left_stick"]["down"]])

            # Buttons
            for button in config_json["buttons"].keys():
                eval_key('buttons', button)
            

            time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()