import json
import time
from pathlib import Path

import pygame
from pynput.keyboard import Controller, Key


DEADZONE = 0.1
LOOP_DELAY = 0.01
DPAD_INITIAL_DELAY = 0.01
DPAD_REPEAT_DELAY = 0.15

CONFIG_PATH = Path(__file__).with_name("config.json")
KEYBOARD_MAP_PATH = Path(__file__).with_name("keyboard_map.json")


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_nested(mapping, *keys):
    value = mapping
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
        if value is None:
            return None
    return value


def resolve_key(key_name):
    if key_name is None or key_name == "None":
        return None
    return getattr(Key, key_name, key_name)


class KeyboardState:
    def __init__(self):
        self.keyboard = Controller()
        self.pressed_keys = set()

    def set_pressed(self, key, should_press):
        if key is None:
            return

        if should_press and key not in self.pressed_keys:
            self.keyboard.press(key)
            self.pressed_keys.add(key)
        elif not should_press and key in self.pressed_keys:
            self.keyboard.release(key)
            self.pressed_keys.remove(key)

    def release_all(self):
        for key in list(self.pressed_keys):
            self.keyboard.release(key)
            self.pressed_keys.remove(key)


def init_joystick(index=0):
    pygame.init()
    pygame.joystick.init()

    joystick_count = pygame.joystick.get_count()
    if joystick_count == 0:
        raise RuntimeError("No joystick detected")
    if index >= joystick_count:
        raise RuntimeError(f"Joystick index {index} not found; detected {joystick_count}")

    joystick = pygame.joystick.Joystick(index)
    joystick.init()
    print(f"Joystick detected: {joystick.get_name()}")
    return joystick


def sync_button(joystick, keyboard_state, config, keyboard_map, button_name):
    button_index = get_nested(config, "buttons", button_name)
    key_name = get_nested(keyboard_map, "buttons", button_name)
    key = resolve_key(key_name)

    if button_index is None or key is None:
        return

    keyboard_state.set_pressed(key, joystick.get_button(button_index))


def sync_direction(keyboard_state, keyboard_map, direction, value, active):
    key = resolve_key(get_nested(keyboard_map, "axes", "left_stick", direction))
    keyboard_state.set_pressed(key, active(value))


def read_axis_with_fallback(joystick, primary_axis, fallback_axis):
    value = joystick.get_axis(primary_axis)
    if abs(value) > DEADZONE or fallback_axis is None:
        return value
    return joystick.get_axis(fallback_axis)


def apply_hat_repeat(axis_value, hat_value, start_time, timeout):
    if not hat_value:
        return axis_value, time.monotonic(), DPAD_INITIAL_DELAY

    now = time.monotonic()
    if now - start_time > timeout:
        return hat_value if abs(axis_value) <= DEADZONE else axis_value, now, DPAD_REPEAT_DELAY

    return axis_value, start_time, timeout


def main():
    config = load_json(CONFIG_PATH)
    keyboard_map = load_json(KEYBOARD_MAP_PATH)
    keyboard_state = None
    joystick = None

    x_hat_timeout = DPAD_INITIAL_DELAY
    y_hat_timeout = DPAD_INITIAL_DELAY
    x_hat_start = time.monotonic()
    y_hat_start = time.monotonic()

    try:
        keyboard_state = KeyboardState()
        joystick = init_joystick()

        while True:
            pygame.event.pump()

            left_x_axis = get_nested(config, "axes", "left_stick", "left_right")
            left_y_axis = get_nested(config, "axes", "left_stick", "up_down")
            right_y_axis = get_nested(config, "axes", "right_stick", "up_down")

            x = joystick.get_axis(left_x_axis)
            y = read_axis_with_fallback(joystick, left_y_axis, right_y_axis)

            hat = joystick.get_hat(0)
            x_hat = hat[get_nested(config, "hats", "left_right")]
            y_hat = -1 * hat[get_nested(config, "hats", "up_down")]

            x, x_hat_start, x_hat_timeout = apply_hat_repeat(
                x, x_hat, x_hat_start, x_hat_timeout
            )
            y, y_hat_start, y_hat_timeout = apply_hat_repeat(
                y, y_hat, y_hat_start, y_hat_timeout
            )

            sync_direction(
                keyboard_state, keyboard_map, "left", x, lambda val: val < -DEADZONE
            )
            sync_direction(
                keyboard_state, keyboard_map, "right", x, lambda val: val > DEADZONE
            )
            sync_direction(
                keyboard_state, keyboard_map, "up", y, lambda val: val < -DEADZONE
            )
            sync_direction(
                keyboard_state, keyboard_map, "down", y, lambda val: val > DEADZONE
            )

            for button_name in config["buttons"]:
                sync_button(joystick, keyboard_state, config, keyboard_map, button_name)

            time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        pass
    except pygame.error as error:
        print(f"Joystick error: {error}")
    finally:
        if keyboard_state is not None:
            keyboard_state.release_all()
        if joystick is not None:
            joystick.quit()
        pygame.quit()


if __name__ == "__main__":
    main()
