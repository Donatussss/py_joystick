import pygame
from time import sleep

pygame.init()
pygame.joystick.init()

js = pygame.joystick.Joystick(0)
js.init()

print("Axes:", js.get_numaxes())
print("Buttons:", js.get_numbuttons())
print("Hats:", js.get_numhats())

while True:
    pygame.event.pump()

    axes = [js.get_axis(i) for i in range(js.get_numaxes())]
    buttons = [js.get_button(i) for i in range(js.get_numbuttons())]
    hats = [js.get_hat(i) for i in range(js.get_numhats())]

    print("Axes:", axes, "Buttons:", buttons, "Hats (D-pad):", hats)
    sleep(1)
