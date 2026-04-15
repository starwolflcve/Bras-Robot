from machine import Pin, PWM
from time import sleep

# Initialisation du servo sur la broche GP0
servo = PWM(Pin(8))
servo.freq(50)  # Fréquence 50Hz pour le SG90

def angle_to_duty(angle):
    # SG90 : 0° = 1ms, 180° = 2ms sur une période de 20ms (50Hz)
    # Duty cycle en 16 bits (0-65535)
    min_duty = 1638   # ~1ms  (0°)
    max_duty = 8192   # ~2ms  (180°)
    return int(min_duty + (angle / 180) * (max_duty - min_duty))

def set_angle(angle):
    servo.duty_u16(angle_to_duty(angle))

# Position centrale de départ (90°)
set_angle(90)
sleep(1)

print("Démarrage oscillation 30° gauche/droite...")

while True:
    # Tourne à droite (90° + 30° = 120°)
    print("→ Droite : 120°")
    set_angle(120)
    sleep(1)

    # Tourne à gauche (90° - 30° = 60°)
    print("← Gauche : 60°")
    set_angle(45)
    sleep(1)
    