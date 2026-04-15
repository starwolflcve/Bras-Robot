# 🦾 BRAS-ROBOT

> Bras robot articulé à 4 axes, contrôlé sans fil via 2 joysticks — ESP32 + MicroPython + ESP-NOW

---

## 📋 Description

**BRAS-ROBOT** est un bras robotique articulé contrôlé à distance grâce à une manette sans fil maison. Le système repose sur deux ESP32 communicant via le protocole **ESP-NOW** (Wi-Fi sans routeur) :

- **ESP32-C3** → embarqué sur le bras, pilote les 4 servos
- **ESP32-WROOM-32** → dans la manette, lit les 2 joysticks et envoie les données

---

## 🧩 Composants

| Composant | Qté | Rôle |
|---|---|---|
| ESP32-C3 DevKitC-02 | 1 | Cerveau du bras robot (récepteur) |
| ESP32-WROOM-32 | 1 | Cerveau de la manette (émetteur) |
| Servo HS-311 modifié 360° | 1 | Rotation de la base |
| Servo SG90 | 3 | Bras 1, Bras 2, Pince |
| Joystick HW-504 | 2 | Contrôle des 4 axes |
| Breadboard / plaques | 3 | Support de câblage |
| Câbles M-M / M-F | ~20 | Câblage général |
| Câble USB | 1 | Alimentation via PC |

---

## 🔌 Câblage

### Bras Robot (ESP32-C3)

| Servo | Broche ESP32-C3 | Rôle |
|---|---|---|
| HS-311 Base (Signal) | GPIO 3 | Rotation gauche/droite |
| SG90 Bras 1 (Signal) | GPIO 7 | Haut/bas segment 1 |
| SG90 Bras 2 (Signal) | GPIO 8 | Haut/bas segment 2 |
| SG90 Pince (Signal) | GPIO 9 | Ouverture/fermeture |
| Tous les VCC | 5V (VBUS) | Alimentation servos |
| Tous les GND | GND | Masse commune |

### Manette (ESP32-WROOM-32)

| Joystick | Broche | GPIO | Rôle |
|---|---|---|---|
| J1 | VRX | 33 | Rotation base |
| J1 | VRY | 32 | Bras 1 |
| J1 | SW | 25 | Reset base + bras 1 |
| J2 | VRX | 34 | Bras 2 |
| J2 | VRY | 35 | Pince |
| J2 | SW | 26 | Reset bras 2 + pince |
| Les deux | VCC | 3V3 | ⚠️ 3.3V uniquement |
| Les deux | GND | GND | Masse |

> ⚠️ **Attention :** Les joysticks s'alimentent en **3.3V**, pas en 5V.

---

## 🕹️ Contrôles

| Action | Joystick | Résultat |
|---|---|---|
| Axe X ↑↓ | J1 | Rotation base (HS-311 360°) |
| Axe Y ←→ | J1 | Bras 1 (0° → 180°) |
| Axe X ↑↓ | J2 | Bras 2 (0° → 180°) |
| Axe Y ←→ | J2 | Pince (0° → 180°) |
| Bouton SW1 | J1 | Reset base + bras 1 à 0° |
| Bouton SW2 | J2 | Reset bras 2 + pince à 0° |

---

## 🚀 Installation & Lancement

### Prérequis

- [Thonny IDE](https://thonny.org/) pour flasher les ESP32
- MicroPython installé sur les deux ESP32
  - [Firmware ESP32-C3](https://micropython.org/download/ESP32_GENERIC_C3/)
  - [Firmware ESP32-WROOM-32](https://micropython.org/download/ESP32_GENERIC/)

### Étape 1 — Récupérer l'adresse MAC du bras robot

Avant de flasher la manette, il faut connaître l'adresse MAC de l'ESP32-C3 (bras).

Branchez l'ESP32-C3 et exécutez ce script dans le REPL MicroPython :

```python
import network
w = network.WLAN(network.STA_IF)
w.active(True)
print(w.config('mac'))
```

Notez l'adresse MAC affichée (ex : `b'\x58\xcfy\x05]\xd8'`).

### Étape 2 — Flasher la manette

Dans `codemanette_final.py`, remplacez la ligne `peer_mac` par l'adresse MAC récupérée à l'étape 1 :

```python
peer_mac = b'\x58\xcfy\x05]\xd8'  # ← Remplacer par votre adresse MAC
```

Copiez le fichier sur l'ESP32-WROOM-32 en tant que `main.py`.

### Étape 3 — Flasher le bras robot

Copiez le code du bras robot sur l'ESP32-C3 en tant que `main.py`.

### Étape 4 — Démarrage

1. **Allumez d'abord le bras robot** (ESP32-C3) — il attend la calibration
2. **Allumez ensuite la manette** (ESP32-WROOM-32) **sans toucher aux joysticks**
3. La calibration se fait automatiquement (20 lectures du point de repos)
4. Le message `Pret ! En attente des ordres...` s'affiche → c'est parti !

---

## ⚙️ Fonctionnalités techniques

**Anti-tremblement**
- Moyenne sur 10 lectures ADC par cycle
- Zone morte de ±200 autour du point de repos
- Le servo ne bouge que si le déplacement dépasse 2°

**Mémoire de position**
- Quand le joystick est au repos, le servo conserve sa dernière position
- Pas de retour automatique à 0°

**Calibration automatique au démarrage**
- 20 lectures à vide pour détecter le point neutre de chaque axe
- S'adapte aux variations propres à chaque joystick

**Communication sans fil ESP-NOW**
- Latence ~20ms
- Pas besoin de réseau Wi-Fi ni de routeur
- Paquet de 10 octets : 4 valeurs ADC (int16) + 2 boutons (byte)

---

## 🔋 Alimentation

- **Servos** → alimentés en **5V** via le VBUS de l'ESP32-C3 (câble USB)
- **Joysticks** → alimentés en **3.3V** via la broche 3V3 de l'ESP32-WROOM-32
- **ESP32** → alimentés via câble USB (PC ou chargeur 5V)

> 💡 Si les servos manquent de puissance, préférez une alimentation externe 5V dédiée sur la breadboard plutôt que de tout tirer depuis l'USB.
