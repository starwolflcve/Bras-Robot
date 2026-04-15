# ============================================================
#  BRAS ROBOT - ESP32-C3 DevKitC-02 - MicroPython
#  4 axes : Base + Bras1 + Bras2 + Pince
#  Contrôle : 2 joysticks HW-504 (ADC + bouton)
# ============================================================
 
from machine import Pin, PWM, ADC
import time
 
# ============================================================
# CONFIGURATION PINS
# ============================================================
PIN_SERVO_BASE  = 3   # Servo Base
PIN_SERVO_BRAS1 = 7   # SG90 Bras 1
PIN_SERVO_BRAS2 = 8   # SG90 Bras 2
PIN_SERVO_PINCE = 9   # SG90 Pince
 
PIN_J1_X = 0   # ADC0 - Joystick 1 axe X -> Base
PIN_J1_Y = 1   # ADC1 - Joystick 1 axe Y -> Bras 1
PIN_J1_SW = 5  # [CORRIGÉ] Bouton J1 sur GPIO 5
 
PIN_J2_X = 4   # ADC4 - Joystick 2 axe X -> Bras 2
PIN_J2_Y = 2   # [CORRIGÉ] ADC2 sur GPIO 2 -> Pince
PIN_J2_SW = 6  # Bouton J2
 
# ============================================================
# PARAMÈTRES PWM
# ============================================================
FREQ_SERVO = 50          # 50 Hz
MIN_DUTY   = 1638        # ~0.5ms -> 0°
MAX_DUTY   = 8192        # ~2.5ms -> 180°
 
# ============================================================
# PARAMÈTRES ADC & MOUVEMENT
# ============================================================
ADC_MAX  = 4095
DEAD_ZONE = 200          # Zone morte pour éviter les tremblements
NB_SMOOTH = 10           # Lissage ADC
NB_CALIB  = 20           # Calibration au démarrage

# Vitesse de déplacement (plus la valeur est haute, plus le bras va vite)
MAX_STEP_ANGLE = 2.5     
 
# ============================================================
# INITIALISATION
# ============================================================
pwm_base  = PWM(Pin(PIN_SERVO_BASE),  freq=FREQ_SERVO)
pwm_bras1 = PWM(Pin(PIN_SERVO_BRAS1), freq=FREQ_SERVO)
pwm_bras2 = PWM(Pin(PIN_SERVO_BRAS2), freq=FREQ_SERVO)
pwm_pince = PWM(Pin(PIN_SERVO_PINCE), freq=FREQ_SERVO)
 
adc_j1x = ADC(Pin(PIN_J1_X))
adc_j1y = ADC(Pin(PIN_J1_Y))
adc_j2x = ADC(Pin(PIN_J2_X))
adc_j2y = ADC(Pin(PIN_J2_Y))
 
adc_j1x.atten(ADC.ATTN_11DB)
adc_j1y.atten(ADC.ATTN_11DB)
adc_j2x.atten(ADC.ATTN_11DB)
adc_j2y.atten(ADC.ATTN_11DB)
 
sw1 = Pin(PIN_J1_SW, Pin.IN, Pin.PULL_UP)
sw2 = Pin(PIN_J2_SW, Pin.IN, Pin.PULL_UP)
 
# ============================================================
# FONCTIONS DE CONTRÔLE
# ============================================================
 
def set_angle(pwm, angle):
    """Envoie l'angle (0-180) au servo."""
    angle = max(0, min(180, angle))
    duty = int(MIN_DUTY + (MAX_DUTY - MIN_DUTY) * angle / 180)
    pwm.duty_u16(duty)
 
def calibrer():
    print("Calibration... ne touchez pas aux joysticks")
    sx1, sy1, sx2, sy2 = 0, 0, 0, 0
    for _ in range(NB_CALIB):
        sx1 += adc_j1x.read(); sy1 += adc_j1y.read()
        sx2 += adc_j2x.read(); sy2 += adc_j2y.read()
        time.sleep_ms(10)
    return sx1//NB_CALIB, sy1//NB_CALIB, sx2//NB_CALIB, sy2//NB_CALIB
 
def read_smooth(adc):
    t = 0
    for _ in range(NB_SMOOTH): t += adc.read()
    return t // NB_SMOOTH

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
# BOUCLE PRINCIPALE
# ============================================================
 
def main():
    print("Démarrage du Bras Robot")
    
    # Position de départ (tous à 90° ou 0° selon ton choix)
    angle_base  = 90.0
    angle_bras1 = 0.0
    angle_bras2 = 0.0
    angle_pince = 0.0
    
    # Appliquer positions initiales
    set_angle(pwm_base, angle_base)
    set_angle(pwm_bras1, angle_bras1)
    set_angle(pwm_bras2, angle_bras2)
    set_angle(pwm_pince, angle_pince)
    
    rx1, ry1, rx2, ry2 = calibrer()
    
    sw1_last, sw2_last = True, True
 
    while True:
        # Lecture des joysticks
        v1x = read_smooth(adc_j1x); v1y = read_smooth(adc_j1y)
        v2x = read_smooth(adc_j2x); v2y = read_smooth(adc_j2y)
 
        # Calcul des déplacements (steps)
        s_base  = adc_to_step(v1x, rx1)
        s_bras1 = adc_to_step(v1y, ry1)
        s_bras2 = adc_to_step(v2x, rx2)
        s_pince = adc_to_step(v2y, ry2)
 
        # Mise à jour des angles et envoi aux servos
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
        if not sw1.value() and sw1_last:
            angle_base, angle_bras1 = 90.0, 0.0
            set_angle(pwm_base, 90); set_angle(pwm_bras1, 0)
            print("Reset J1")
        sw1_last = sw1.value()
 
        if not sw2.value() and sw2_last:
            angle_bras2, angle_pince = 0.0, 0.0
            set_angle(pwm_bras2, 0); set_angle(pwm_pince, 0)
            print("Reset J2")
        sw2_last = sw2.value()
 
        time.sleep_ms(20)

if __name__ == "__main__":
    main()
