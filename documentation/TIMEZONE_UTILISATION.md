# 🌍 Utilisation de la Timezone

## 📅 Date: 28 octobre 2025

## ❓ Question Utilisateur

> "Est-ce que la timezone est utilisée ? Quand je la change, ça ne fait rien."

## 🎯 Réponse

La timezone est utilisée **SEULEMENT pour les vidéos de drone** qui ont des métadonnées en **UTC** (temps universel). Pour tous les autres types de fichiers, elle n'a **aucun effet**.

## 📊 Tableau d'Utilisation

| Type de Fichier | Source de Date | Timezone Utilisée? | Raison |
|-----------------|----------------|--------------------|---------| 
| **Vidéo drone** | QuickTime metadata (UTC) | ✅ **OUI** | Conversion UTC → Heure locale |
| **Photo drone** | mtime (local) | ❌ Non | mtime déjà en heure locale système |
| **iPhone/Apple** | exiftool (local) | ❌ Non | exiftool retourne heure locale appareil |
| **Autres caméras** | filename/mtime | ❌ Non | Heure locale de l'appareil ou système |

## 🔍 Détails Techniques

### Vidéos de Drone (Seul cas où timezone est importante)

**Métadonnées des drones DJI**:
```
format.tags.creation_time = "2024-10-15T18:30:00.000000Z"  ← UTC (Z = Zulu time)
```

**Conversion appliquée**:
```python
# Dans extract_times_for_drone_file()
tz = zoneinfo.ZoneInfo(tz_name)  # Ex: "America/Montreal"
dt_metadata_utc = datetime.fromisoformat(iso).astimezone(timezone.utc)
dt_metadata_local = dt_metadata_utc.astimezone(tz)  # Conversion!
```

**Résultat**:
- UTC: `2024-10-15 18:30:00Z`
- Montreal (UTC-4): `2024-10-15 14:30:00` ← Date utilisée pour organiser!

### Photos de Drone

**Source**: mtime (modification time du fichier)

```python
ts = p.stat().st_mtime  # Timestamp système
dt = datetime.fromtimestamp(ts)  # Déjà en heure locale du système
```

**Pourquoi pas de conversion?**
- Le mtime est un timestamp Unix (secondes depuis 1970)
- `fromtimestamp()` le convertit en heure **locale du système**
- Pas de métadonnées UTC à convertir

**Note**: Si vous avez copié les fichiers depuis une carte SD, le mtime est l'heure de copie (système), pas l'heure de prise de vue originale.

### iPhone/Apple (Exiftool)

**Métadonnées iPhone**:
```
DateTimeOriginal: 2024-10-15 14:30:00
CreationDate: 2024-10-15 14:30:00
```

**Pas de timezone**:
- Les métadonnées EXIF sont généralement en **heure locale** de l'appareil
- Pas de marqueur UTC (`Z`) → pas de conversion nécessaire
- L'heure est celle du réglage de l'iPhone au moment de la photo

### Autres Caméras

**Sources**:
1. **Filename**: `IMG_20241015_143000.jpg` → Heure locale de la caméra
2. **mtime**: Heure de copie ou modification → Heure locale du système

**Pas de conversion** car pas de métadonnées UTC.

## 🎬 Exemple Concret

### Configuration
```bash
python organize_footage_links.py project --tz "America/Montreal"
```

### Fichiers Testés

#### 1. Vidéo Drone DJI
```
Fichier: DJI_0001.MP4
Metadata: creation_time = "2024-10-15T18:30:00.000000Z" (UTC)
Timezone: America/Montreal (UTC-4)

Calcul:
  18:30 UTC - 4h = 14:30 heure locale
  
Résultat: video/2024-10-15/14h30m00s_dji_DJI_0001.json
          ✅ Timezone utilisée!
```

#### 2. Photo Drone DJI
```
Fichier: DJI_0002.JPG
Source: mtime = 2024-10-15 14:35:00 (heure locale système)
Timezone: America/Montreal (ignorée)

Résultat: photo/2024-10-15/14h35m00s_dji_DJI_0002.json
          ❌ Timezone ignorée (mtime déjà local)
```

#### 3. Photo iPhone
```
Fichier: IMG_1234.HEIC
Metadata: DateTimeOriginal = 2024-10-15 14:40:00 (local iPhone)
Timezone: America/Montreal (ignorée)

Résultat: photo/2024-10-15/14h40m00s_iphone_IMG_1234.json
          ❌ Timezone ignorée (EXIF déjà local)
```

#### 4. Vidéo Canon
```
Fichier: MVI_1234.MOV
Source: filename → 20241015_144500
Timezone: America/Montreal (ignorée)

Résultat: video/2024-10-15/14h45m00s_canon_MVI_1234.json
          ❌ Timezone ignorée (filename local)
```

## ⚠️ Quand Changer la Timezone?

### ✅ Utile Si:
Vous avez des **vidéos de drone DJI** prises dans un fuseau horaire différent de votre fuseau par défaut.

**Exemple**: 
- Voyage à Paris (timezone `Europe/Paris`)
- Vidéos drone avec métadonnées UTC
- Vous voulez organiser par heure locale parisienne

```bash
python organize_footage_links.py project --tz "Europe/Paris"
```

### ❌ Inutile Si:
- Vous n'avez **que des photos** (toutes utilisent mtime ou EXIF local)
- Vous n'avez **pas de drones DJI**
- Vos drones sont déjà configurés en heure locale (pas UTC)

## 🔧 Solution Alternative: Ajustement Temporel

Si vous voulez ajuster les dates/heures de **n'importe quel groupe**, utilisez plutôt **l'ajustement temporel**:

```json
{
    "dji_drone": "+00000000_040000"
}
```

Cela ajoute 4 heures à **tous** les fichiers du groupe `dji_drone` (vidéos ET photos), équivalent à un décalage UTC-4.

**Avantages**:
- ✅ Fonctionne pour **vidéos ET photos**
- ✅ Fonctionne pour **tous types de fichiers**
- ✅ Plus flexible (peut ajuster jours, heures, minutes)

## 📋 Recommandations

### Pour les Vidéos Drone
1. **Si métadonnées UTC**: Utiliser `--tz` approprié
2. **Si métadonnées déjà locales**: Pas besoin de timezone
3. **Si incertitude**: Essayer avec un fichier et vérifier le résultat

### Pour les Photos Drone
1. **Utiliser l'ajustement temporel** si les dates sont incorrectes
2. Ne pas compter sur `--tz` (n'a pas d'effet)

### Pour Autres Fichiers
1. **Ajustement temporel** si nécessaire
2. La timezone n'a aucun effet

## 🧪 Test pour Vérifier

### Créer un fichier de test
```bash
# Créer une structure de test
mkdir -p test_project/Footage_raw/dji_test
# Copier une vidéo drone dedans
```

### Tester avec différentes timezones
```bash
# Test 1: Montreal
python organize_footage_links.py test_project --tz "America/Montreal"
# Regarder l'heure du fichier organisé

# Test 2: Paris
rm -rf test_project/Footage_metadata_sorted
python organize_footage_links.py test_project --tz "Europe/Paris"
# Regarder l'heure du fichier organisé - devrait être différente si UTC!
```

### Résultat Attendu
- **Si l'heure change**: Métadonnées UTC, timezone fonctionne ✅
- **Si l'heure ne change pas**: Métadonnées déjà locales ou pas de métadonnées, timezone ignorée ❌

## 📚 Voir Aussi

- **[GUIDE_AJUSTEMENT_TEMPS.md](GUIDE_AJUSTEMENT_TEMPS.md)** - Alternative flexible pour ajuster dates
- **[DRONE_PHOTOS_MTIME.md](DRONE_PHOTOS_MTIME.md)** - Pourquoi photos utilisent mtime
- **[README.md](../README.md)** - Section "Timezone Configuration"

## 🎯 Résumé

| Question | Réponse |
|----------|---------|
| La timezone est-elle utilisée? | **Oui, mais seulement pour vidéos drone** |
| Pourquoi ça ne fait rien quand je la change? | Probablement pas de vidéos drone, ou métadonnées déjà locales |
| Alternative? | **Ajustement temporel** (fonctionne pour tout) |
| Comment tester? | Comparer résultats avec différentes timezones |

---

**Date**: 28 octobre 2025  
**Réponse**: Timezone limitée aux vidéos drone avec métadonnées UTC  
**Alternative**: Ajustement temporel par groupe (plus flexible)
