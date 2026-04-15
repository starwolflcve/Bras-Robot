# ============================================================
#  BRAS ROBOT - ESP32-C3 DevKitC-02 - MicroPython
#  4 axes : Base HS-311 360° + Bras1 + Bras2 + Pince SG90
#  Contrôle : 2 joysticks HW-504 (ADC + bouton)
# ============================================================
 
from machine import Pin, PWM, ADC
import time
 
# ============================================================
# CONFIGURATION PINS
# ============================================================
PIN_SERVO_BASE  = 3   # HS-311 360° (servo continu)
PIN_SERVO_BRAS1 = 7   # SG90 Bras 1
PIN_SERVO_BRAS2 = 8   # SG90 Bras 2
PIN_SERVO_PINCE = 9   # SG90 Pince
 
PIN_J1_X = 0   # ADC0 - Joystick 1 axe X → Base rotation
PIN_J1_Y = 1   # ADC1 - Joystick 1 axe Y → Bras 1

# --- CORRECTION ICI ---
PIN_J2_Y = 2   # ADC2 (maintenant sur GPIO 2, qui est sur l'ADC1) → Pince
PIN_J2_X = 4   # ADC4 - Joystick 2 axe X → Bras 2

PIN_J1_SW = 5  # Bouton J1 (déplacé sur GPIO 5 en entrée numérique) → Reset base + bras 1
PIN_J2_SW = 6  # Bouton J2 → Reset bras 2 + pince
 
# ============================================================
# PARAMÈTRES PWM
# ============================================================
FREQ_SERVO = 50          # 50 Hz standard pour servos
MIN_DUTY   = 1638        # ~0.5ms  → 0°   (sur 65535)
MAX_DUTY   = 8192        # ~2.5ms  → 180° (sur 65535)
MID_DUTY   = (MIN_DUTY + MAX_DUTY) // 2  # ~1.5ms → 90°
 
# HS-311 360° : point mort (servo immobile)
# Ajuster si le servo tourne en position repos
STOP_DUTY  = 4915        # ~1.5ms ≈ 77 en 0-127 → à calibrer
STOP_DUTY_MIN = 4800     # Limite basse du point mort acceptable
STOP_DUTY_MAX = 5030     # Limite haute du point mort acceptable
 
# ============================================================
# PARAMÈTRES ADC
# ============================================================
ADC_MIN  = 0
ADC_MAX  = 4095          # 12 bits
DEAD_ZONE = 150          # Zone morte autour du point de repos
ANGLE_CHANGE_MIN = 2     # Changement minimum (°) pour bouger le servo
NB_SMOOTH = 10           # Nombre de lectures pour lissage
NB_CALIB  = 20           # Nombre de lectures pour calibration repos
 
# ============================================================
# INITIALISATION SERVOS
# ============================================================
pwm_base  = PWM(Pin(PIN_SERVO_BASE),  freq=FREQ_SERVO)
pwm_bras1 = PWM(Pin(PIN_SERVO_BRAS1), freq=FREQ_SERVO)
pwm_bras2 = PWM(Pin(PIN_SERVO_BRAS2), freq=FREQ_SERVO)
pwm_pince = PWM(Pin(PIN_SERVO_PINCE), freq=FREQ_SERVO)
 
# ============================================================
# INITIALISATION ADC (joysticks)
# ============================================================
adc_j1x = ADC(Pin(PIN_J1_X))
adc_j1y = ADC(Pin(PIN_J1_Y))
adc_j2x = ADC(Pin(PIN_J2_X))
adc_j2y = ADC(Pin(PIN_J2_Y))
 
# Atténuation 11dB → plage 0–3.3V mesurable sur 0–4095
adc_j1x.atten(ADC.ATTN_11DB)
adc_j1y.atten(ADC.ATTN_11DB)
adc_j2x.atten(ADC.ATTN_11DB)
adc_j2y.atten(ADC.ATTN_11DB)
 
# ============================================================
# INITIALISATION BOUTONS (pull-up interne, actif bas)
# ============================================================
sw1 = Pin(PIN_J1_SW, Pin.IN, Pin.PULL_UP)
sw2 = Pin(PIN_J2_SW, Pin.IN, Pin.PULL_UP)
 
# ============================================================
# FONCTIONS SG90 (0°–180°)
# ============================================================
 
def angle_to_duty(angle):
    """Convertit un angle 0–180° en duty cycle 16 bits."""
    angle = max(0, min(180, angle))
    return int(MIN_DUTY + (MAX_DUTY - MIN_DUTY) * angle / 180)
 
def set_angle(pwm, angle):
    """Positionne un servo SG90 à l'angle demandé."""
    pwm.duty_u16(angle_to_duty(angle))
 
# ============================================================
# FONCTIONS HS-311 360° (servo continu)
# ============================================================
 
def set_servo360(vitesse):
    """
    Contrôle le servo 360°.
    vitesse : -100 (plein gauche) .. 0 (stop) .. +100 (plein droite)
    """
    vitesse = max(-100, min(100, vitesse))
    if vitesse == 0:
        pwm_base.duty_u16(STOP_DUTY)
    elif vitesse > 0:
        # Vers l'avant : STOP → MAX
        duty = int(STOP_DUTY + (MAX_DUTY - STOP_DUTY) * vitesse / 100)
        pwm_base.duty_u16(duty)
    else:
        # Vers l'arrière : STOP → MIN
        duty = int(STOP_DUTY + (STOP_DUTY - MIN_DUTY) * vitesse / 100)
        pwm_base.duty_u16(duty)
 
def stop_servo360():
    """Arrête le servo continu (point mort)."""
    pwm_base.duty_u16(STOP_DUTY)
 
# ============================================================
# CALIBRATION DES JOYSTICKS AU REPOS
# ============================================================
 
def calibrer():
    """
    Lit la position de repos de chaque axe (moyenne NB_CALIB lectures).
    Appeler au démarrage, joysticks en position neutre.
    Retourne (rest_x1, rest_y1, rest_x2, rest_y2).
    """
    print("Calibration : ne pas toucher les joysticks...")
    sum_x1, sum_y1, sum_x2, sum_y2 = 0, 0, 0, 0
    for _ in range(NB_CALIB):
        sum_x1 += adc_j1x.read()
        sum_y1 += adc_j1y.read()
        sum_x2 += adc_j2x.read()
        sum_y2 += adc_j2y.read()
        time.sleep_ms(20)
    rx1 = sum_x1 // NB_CALIB
    ry1 = sum_y1 // NB_CALIB
    rx2 = sum_x2 // NB_CALIB
    ry2 = sum_y2 // NB_CALIB
    print(f"Repos → J1:({rx1},{ry1})  J2:({rx2},{ry2})")
    return rx1, ry1, rx2, ry2
 
# ============================================================
# UTILITAIRES
# ============================================================
 
def read_smooth(adc):
    """Moyenne de NB_SMOOTH lectures pour réduire le bruit ADC."""
    total = 0
    for _ in range(NB_SMOOTH):
        total += adc.read()
    return total // NB_SMOOTH
 
def joystick_bouge(valeur, repos):
    """
    Retourne True si le joystick est sorti de la zone morte.
    zone morte = repos ± DEAD_ZONE
    """
    return abs(valeur - repos) > DEAD_ZONE
 
def adc_to_angle(valeur, repos):
    """
    Convertit une valeur ADC en angle 0°–180° en tenant compte du point de repos.
    Le repos correspond à 90°.
    """
    if valeur >= repos:
        # Repos → MAX : 90° → 180°
        angle = 90 + int(90 * (valeur - repos) / (ADC_MAX - repos))
    else:
        # MIN → Repos : 0° → 90°
        angle = int(90 * valeur / repos)
    return max(0, min(180, angle))
 
def adc_to_vitesse(valeur, repos):
    """
    Convertit une valeur ADC en vitesse -100..+100 pour le servo 360°.
    Le repos correspond à 0 (arrêt).
    """
    delta = valeur - repos
    if abs(delta) <= DEAD_ZONE:
        return 0
    if delta > 0:
        return int(100 * (delta - DEAD_ZONE) / (ADC_MAX - repos - DEAD_ZONE))
    else:
        return int(-100 * (-delta - DEAD_ZONE) / (repos - DEAD_ZONE))
 
# ============================================================
# POSITIONS INITIALES
# ============================================================
 
def init_positions():
    """Met tous les servos à 0° et arrête la base."""
    stop_servo360()
    set_angle(pwm_bras1, 0)
    set_angle(pwm_bras2, 0)
    set_angle(pwm_pince, 0)
    time.sleep_ms(500)
    print("Positions initiales : OK")
 
# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================
 
def main():
    print("=== BRAS ROBOT ESP32-C3 ===")
 
    # Positions initiales
    init_positions()
 
    # Calibration joysticks
    rest_x1, rest_y1, rest_x2, rest_y2 = calibrer()
 
    # Angles courants mémorisés (mémoire de position)
    angle_bras1 = 0
    angle_bras2 = 0
    angle_pince = 0
 
    # Anti-rebond boutons
    sw1_last = True
    sw2_last = True
    DEBOUNCE_MS = 200
    sw1_time = 0
    sw2_time = 0
 
    print("Démarrage boucle principale...")
 
    while True:
        now = time.ticks_ms()
 
        # --- Lecture lissée des 4 axes ---
        val_x1 = read_smooth(adc_j1x)
        val_y1 = read_smooth(adc_j1y)
        val_x2 = read_smooth(adc_j2x)
        val_y2 = read_smooth(adc_j2y)
 
        # ---- BASE 360° (J1 axe X) ----
        vitesse_base = adc_to_vitesse(val_x1, rest_x1)
        set_servo360(vitesse_base)
 
        # ---- BRAS 1 (J1 axe Y) ----
        if joystick_bouge(val_y1, rest_y1):
            nouvel_angle = adc_to_angle(val_y1, rest_y1)
            if abs(nouvel_angle - angle_bras1) >= ANGLE_CHANGE_MIN:
                angle_bras1 = nouvel_angle
                set_angle(pwm_bras1, angle_bras1)
 
        # ---- BRAS 2 (J2 axe X) ----
        if joystick_bouge(val_x2, rest_x2):
            nouvel_angle = adc_to_angle(val_x2, rest_x2)
            if abs(nouvel_angle - angle_bras2) >= ANGLE_CHANGE_MIN:
                angle_bras2 = nouvel_angle
                set_angle(pwm_bras2, angle_bras2)
 
        # ---- PINCE (J2 axe Y) ----
        if joystick_bouge(val_y2, rest_y2):
            nouvel_angle = adc_to_angle(val_y2, rest_y2)
            if abs(nouvel_angle - angle_pince) >= ANGLE_CHANGE_MIN:
                angle_pince = nouvel_angle
                set_angle(pwm_pince, angle_pince)
 
        # ---- BOUTON SW1 → Reset base + bras 1 ----
        sw1_now = sw1.value()
        if not sw1_now and sw1_last and time.ticks_diff(now, sw1_time) > DEBOUNCE_MS:
            sw1_time = now
            print("SW1 : reset base + bras 1")
            stop_servo360()
            angle_bras1 = 0
            set_angle(pwm_bras1, 0)
        sw1_last = sw1_now
 
        # ---- BOUTON SW2 → Reset bras 2 + pince ----
        sw2_now = sw2.value()
        if not sw2_now and sw2_last and time.ticks_diff(now, sw2_time) > DEBOUNCE_MS:
            sw2_time = now
            print("SW2 : reset bras 2 + pince")
            angle_bras2 = 0
            angle_pince = 0
            set_angle(pwm_bras2, 0)
            set_angle(pwm_pince, 0)
        sw2_last = sw2_now
 
        time.sleep_ms(20)   # ~50 Hz de rafraîchissement
 
# ============================================================
# OUTIL DE CALIBRATION DU POINT MORT HS-311 (optionnel)
# Décommenter et flasher séparément pour trouver STOP_DUTY exact
# ============================================================
# def calibrer_stop_hs311():
#     """
#     Balaye les duty cycles autour de 1.5ms pour trouver le point mort exact.
#     Observer le servo : il doit s'arrêter complètement.
#     Noter la valeur et la mettre dans STOP_DUTY.
#     """
#     print("Calibration HS-311 : trouver le point mort")
#     for duty in range(4500, 5200, 10):
#         pwm_base.duty_u16(duty)
#         print(f"duty={duty}")
#         time.sleep_ms(500)
#     stop_servo360()
 
# ============================================================
# POINT D'ENTRÉE
# ============================================================
if __name__ == "__main__":
    main()
