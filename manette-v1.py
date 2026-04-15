# ============================================================
#  MANETTE SANS FIL - ESP32-WROOM-32 - MicroPython
#  Emetteur ESP-NOW vers Bras Robot
# ============================================================

import network
import espnow
import machine
import struct
import time

# ============================================================
# CONFIGURATION PINS (ADC1 uniquement)
# ============================================================
# Joystick 1 (Base & Bras 1)
PIN_J1_X = 33
PIN_J1_Y = 32
PIN_J1_SW = 25

# Joystick 2 (Bras 2 & Pince)
PIN_J2_X = 34
PIN_J2_Y = 35
PIN_J2_SW = 26

# ============================================================
# INITIALISATION
# ============================================================
# ADC
adc_j1x = machine.ADC(machine.Pin(PIN_J1_X))
adc_j1y = machine.ADC(machine.Pin(PIN_J1_Y))
adc_j2x = machine.ADC(machine.Pin(PIN_J2_X))
adc_j2y = machine.ADC(machine.Pin(PIN_J2_Y))

# Atténuation 11dB -> Plage 0-3.3V (valeurs de 0 Ã  4095)
adc_j1x.atten(machine.ADC.ATTN_11DB)
adc_j1y.atten(machine.ADC.ATTN_11DB)
adc_j2x.atten(machine.ADC.ATTN_11DB)
adc_j2y.atten(machine.ADC.ATTN_11DB)

# Boutons (pull-up interne)
sw1 = machine.Pin(PIN_J1_SW, machine.Pin.IN, machine.Pin.PULL_UP)
sw2 = machine.Pin(PIN_J2_SW, machine.Pin.IN, machine.Pin.PULL_UP)

# ============================================================
# CONFIGURATION ESP-NOW
# ============================================================
# L'interface Wi-Fi doit etre active en mode Station
w0 = network.WLAN(network.STA_IF)
w0.active(True)
w0.disconnect()

e = espnow.ESPNow()
e.active(True)

peer_mac = b'X\xcfy\x05]\xd8' 
e.add_peer(peer_mac)

# ============================================================
# BOUCLE PRINCIPALE
# ============================================================
def main():
    print("Manette prÃªte ! DÃ©but de la transmission ESP-NOW...")

    while True:
        # Lecture des 4 axes (0 a 4095)
        val_x1 = adc_j1x.read()
        val_y1 = adc_j1y.read()
        val_x2 = adc_j2x.read()
        val_y2 = adc_j2y.read()
        
        # Lecture des boutons (Inversion : 1 = press, 0 = relacher)
        val_sw1 = 0 if sw1.value() else 1
        val_sw2 = 0 if sw2.value() else 1

        msg = struct.pack('hhhhbb', val_x1, val_y1, val_x2, val_y2, val_sw1, val_sw2)

        # Envoi des données au bras robot
        try:
            e.send(peer_mac, msg)
        except OSError as err:
            pass 

        time.sleep_ms(20) 

if __name__ == "__main__":
    main()
