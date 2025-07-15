import pygame
from gpiozero import Servo
from time import sleep

# Inicializa el servo (ajusta el pin según tu conexión)
servo = Servo(18)  # GPIO18 (PIN12 físico)

# Inicializa pygame y el joystick
pygame.init()
pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print("Joystick:", joystick.get_name())

# El índice del botón RB suele ser 5, pero puedes verificar con esto
BUTTON_RB = 7
NUM_BUTTONS = joystick.get_numbuttons()

try:
    while True:
        pygame.event.pump()

        # Mostrar botones presionados
        for i in range(NUM_BUTTONS):
            if joystick.get_button(i):
                print(f"Botón {i} PRESIONADO")

        # Control del servo con RB
        if joystick.get_button(BUTTON_RB):
            servo.value = 0
        else:
            servo.value = 1

        sleep(0.1)

except KeyboardInterrupt:
    print("Programa terminado")

finally:
    pygame.quit()
