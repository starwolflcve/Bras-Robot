# ============================================================
#  BRAS ROBOT (RECEPTEUR) - ESP32-C3 - MicroPython
#  Controle par ESP-NOW (depuis la manette)
# ============================================================

import machine
import time
import network
import espnow
import struct

# ============================================================
# CONFIGURATION PINS (Seulement les servos maintenant !)
# ============================================================
PIN_SERVO_BASE  = 3   # Servo Base
PIN_SERVO_BRAS1 = 7   # SG90 Bras 1
PIN_SERVO_BRAS2 = 8   # SG90 Bras 2
PIN_SERVO_PINCE = 9   # SG90 Pince

# ============================================================
# PARAMATRES PWM & MOUVEMENT
# ============================================================
FREQ_SERVO = 50          # 50 Hz
MIN_DUTY   = 1638        # ~0.5ms -> 0°
MAX_DUTY   = 8192        # ~2.5ms -> 180°

ADC_MAX  = 4095
DEAD_ZONE = 200          # Zone morte pour éviter les tremblements
MAX_STEP_ANGLE = 2.5     # Vitesse de déplacement

# ============================================================
# INITIALISATION SERVOS
# ============================================================
pwm_base  = machine.PWM(machine.Pin(PIN_SERVO_BASE),  freq=FREQ_SERVO)
pwm_bras1 = machine.PWM(machine.Pin(PIN_SERVO_BRAS1), freq=FREQ_SERVO)
pwm_bras2 = machine.PWM(machine.Pin(PIN_SERVO_BRAS2), freq=FREQ_SERVO)
pwm_pince = machine.PWM(machine.Pin(PIN_SERVO_PINCE), freq=FREQ_SERVO)

def set_angle(pwm, angle):
    """Envoie l'angle (0-180) au servo."""
    angle = max(0, min(180, angle))
    duty = int(MIN_DUTY + (MAX_DUTY - MIN_DUTY) * angle / 180)
    pwm.duty_u16(duty)

def adc_to_step(valeur, repos):
    """Calcule de combien on doit augmenter/diminuer l'angle."""
    delta = valeur - repos
    if abs(delta) <= DEAD_ZONE:
        return 0.0
    if delta > 0:
        return MAX_STEP_ANGLE * (delta - DEAD_ZONE) / (ADC_MAX - repos - DEAD_ZONE)
    else:
        return MAX_STEP_ANGLE * (delta + DEAD_ZONE) / (repos - DEAD_ZONE)

# ============================================================
# INITIALISATION ESP-NOW (RECEPTEUR)
# ============================================================
w0 = network.WLAN(network.STA_IF)
w0.active(True)
w0.disconnect()

e = espnow.ESPNow()
e.active(True)

# ============================================================
# CALIBRATION DE DISTANCE
# ============================================================
def calibrer_distance():
    print("En attente de la manette pour la calibration...")
    print("Allumez la manette sans toucher aux joysticks !")
    sx1, sy1, sx2, sy2 = 0, 0, 0, 0
    lectures = 0
    
    while lectures < 20:
        host, msg = e.recv(timeout_ms=100) 
        if msg:
            v1x, v1y, v2x, v2y, sw1, sw2 = struct.unpack('hhhhbb', msg)
            sx1 += v1x; sy1 += v1y; sx2 += v2x; sy2 += v2y
            lectures += 1
            
    print("Calibration a distance OK !")
    return sx1//20, sy1//20, sx2//20, sy2//20

# ============================================================
# BOUCLE PRINCIPALE
# ============================================================
def main():
    print("=== Demarrage Recepteur Bras Robot ===")
    
    # Positions de depart
    angle_base  = 90.0
    angle_bras1 = 0.0
    angle_bras2 = 0.0
    angle_pince = 0.0
    
    set_angle(pwm_base, angle_base)
    set_angle(pwm_bras1, angle_bras1)
    set_angle(pwm_bras2, angle_bras2)
    set_angle(pwm_pince, angle_pince)
    
    rx1, ry1, rx2, ry2 = calibrer_distance()
    
    sw1_last = 0
    sw2_last = 0
    
    print("Pret ! En attente des ordres de la manette...")

    while True:
        host, msg = e.recv(timeout_ms=20)
        
        if msg:
            v1x, v1y, v2x, v2y, sw1, sw2 = struct.unpack('hhhhbb', msg)
            
            s_base  = adc_to_step(v1x, rx1)
            s_bras1 = adc_to_step(v1y, ry1)
            s_bras2 = adc_to_step(v2x, rx2)
            s_pince = adc_to_step(v2y, ry2)
     
            if s_base != 0:
                angle_base = max(0, min(180, angle_base + s_base))
                set_angle(pwm_base, int(angle_base))
                
            if s_bras1 != 0:
                angle_bras1 = max(0, min(180, angle_bras1 + s_bras1))
                set_angle(pwm_bras1, int(angle_bras1))
                
            if s_bras2 != 0:
                angle_bras2 = max(0, min(180, angle_bras2 + s_bras2))
                set_angle(pwm_bras2, int(angle_bras2))
                
            if s_pince != 0:
                angle_pince = max(0, min(180, angle_pince + s_pince))
                set_angle(pwm_pince, int(angle_pince))
     
            # --- Gestion des boutons Reset ---
            if sw1 == 1 and sw1_last == 0:
                angle_base, angle_bras1 = 90.0, 0.0
                set_angle(pwm_base, 90)
                set_angle(pwm_bras1, 0)
                print("Reset J1 via Manette")
            sw1_last = sw1
     
            if sw2 == 1 and sw2_last == 0:
                angle_bras2, angle_pince = 0.0, 0.0
                set_angle(pwm_bras2, 0)
                set_angle(pwm_pince, 0)
                print("Reset J2 via Manette")
            sw2_last = sw2

if __name__ == "__main__":
    main()
