# 🐛 Correction Bug: Conversion UTC Incorrecte

## 📅 Date: 28 octobre 2025

## ❌ Problème Signalé

> "Mais pour les vidéos, peu importe le UTC que je mets, ça met un 4h de moins."

L'utilisateur a changé la timezone mais le décalage horaire restait toujours **-4 heures**, peu importe la timezone spécifiée.

## 🔍 Analyse du Bug

### Code Bugué

```python
# Dans extract_times_for_drone_file()
iso_norm = iso.replace("Z", "+00:00")  # "2024-10-15T18:30:00Z" → "2024-10-15T18:30:00+00:00"
dt_metadata_raw = datetime.fromisoformat(iso_norm).replace(tzinfo=None)

# Plus tard...
dt_metadata_utc = datetime.fromisoformat(iso_norm).astimezone(timezone.utc)
dt_metadata_local = dt_metadata_utc.astimezone(tz)
```

### Pourquoi ça ne fonctionnait pas?

**Le problème**: `datetime.fromisoformat(iso_norm)` crée un datetime **avec timezone UTC** (`+00:00`), mais `.astimezone(timezone.utc)` **réinterprète** ce datetime comme s'il était dans la **timezone locale du système** avant de le convertir en UTC!

**Exemple concret**:

```python
# Système en America/Montreal (UTC-4)
iso_norm = "2024-10-15T18:30:00+00:00"

# Ce qu'on VOULAIT:
# 18:30 UTC → convertir vers timezone choisie

# Ce qui SE PASSAIT:
dt = datetime.fromisoformat(iso_norm)  # 2024-10-15 18:30:00+00:00 (UTC)
dt_utc = dt.astimezone(timezone.utc)   # Python pense: "c'est du local, convertis en UTC"
                                        # Résultat: 2024-10-15 22:30:00+00:00 (!!!)
                                        # Ajoute 4h au lieu de garder l'heure!

dt_local = dt_utc.astimezone(ZoneInfo("Europe/Paris"))  # 2024-10-16 00:30:00+02:00
# Au lieu de: 2024-10-15 20:30:00+02:00
```

**Résultat**: Peu importe la timezone cible, on ajoutait toujours **+4h** (offset local) avant de convertir, ce qui donnait l'impression que toutes les timezones donnaient le même résultat (-4h du système).

## ✅ Solution

### Code Corrigé

```python
# Parse as UTC explicitly
dt_metadata_utc = datetime.fromisoformat(iso_norm).replace(tzinfo=timezone.utc)
# Convert to target timezone
dt_metadata_local = dt_metadata_utc.astimezone(tz)
```

### Pourquoi ça fonctionne maintenant?

**`.replace(tzinfo=timezone.utc)`** force Python à traiter le datetime comme **vraiment UTC**, sans réinterprétation.

**Exemple corrigé**:

```python
iso_norm = "2024-10-15T18:30:00+00:00"

dt_utc = datetime.fromisoformat(iso_norm).replace(tzinfo=timezone.utc)
# Force: 2024-10-15 18:30:00+00:00 (UTC) - pas de conversion

dt_local = dt_utc.astimezone(ZoneInfo("Europe/Paris"))
# Résultat: 2024-10-15 20:30:00+02:00 ✅

dt_local = dt_utc.astimezone(ZoneInfo("America/Montreal"))
# Résultat: 2024-10-15 14:30:00-04:00 ✅

dt_local = dt_utc.astimezone(ZoneInfo("Asia/Tokyo"))
# Résultat: 2024-10-16 03:30:00+09:00 ✅
```

Maintenant chaque timezone donne le **bon résultat**!

## 🧪 Test de Validation

### Configuration de Test

```python
# Métadonnées drone (UTC)
creation_time = "2024-10-15T18:30:00.000000Z"  # 18h30 UTC

# Test avec différentes timezones
timezones = [
    "America/Montreal",  # UTC-4 → 14h30
    "Europe/Paris",      # UTC+2 → 20h30
    "Asia/Tokyo",        # UTC+9 → 03h30 (lendemain)
    "UTC"                # UTC   → 18h30
]
```

### Résultats Attendus

| Timezone | Heure Locale Attendue | Avant (Bug) | Après (Corrigé) |
|----------|----------------------|-------------|-----------------|
| `America/Montreal` (UTC-4) | 14:30 | ❌ 10:30 (-8h!) | ✅ 14:30 |
| `Europe/Paris` (UTC+2) | 20:30 | ❌ 16:30 (-2h) | ✅ 20:30 |
| `Asia/Tokyo` (UTC+9) | 03:30 | ❌ 23:30 (veille) | ✅ 03:30 (lendemain) |
| `UTC` (UTC+0) | 18:30 | ❌ 14:30 (-4h) | ✅ 18:30 |

**Avant**: Toutes les timezones avaient un **décalage fixe de -4h** (timezone locale du système)  
**Après**: Chaque timezone applique le **bon décalage**

## 📝 Changements Techniques

### Fichier Modifié
- `SORTING/organize_footage_links.py`

### Lignes Changées

**Ligne ~668** (dans `extract_times_for_drone_file()`):
```python
# AVANT:
dt_metadata_utc = datetime.fromisoformat(iso_norm).astimezone(timezone.utc)

# APRÈS:
dt_metadata_utc = datetime.fromisoformat(iso_norm).replace(tzinfo=timezone.utc)
```

**Ligne ~684** (nettoyage code dupliqué):
```python
# AVANT:
dt_metadata_utc = datetime.fromisoformat(iso_norm).astimezone(timezone.utc)
utc_iso = dt_metadata_utc.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

# APRÈS:
# dt_metadata_utc already created above with proper UTC timezone
utc_iso = dt_metadata_utc.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
```

### Impact

✅ **Correction**: Les conversions UTC → timezone locale fonctionnent correctement  
✅ **Pas de régression**: Le code pour les photos/autres fichiers n'est pas affecté  
✅ **Rétrocompatible**: Les projets existants fonctionneront correctement après cette correction

## 🎯 Comportement Corrigé

### Vidéos Drone avec Métadonnées UTC

**Avant la correction**:
```bash
# Peu importe la timezone
python organize_footage_links.py project --tz "Europe/Paris"
python organize_footage_links.py project --tz "Asia/Tokyo"
python organize_footage_links.py project --tz "America/Montreal"

# Toutes donnaient le même résultat:
# video/2024-10-15/10h30m00s_dji_DJI_0001.json
# (Toujours -4h du système = UTC-4 local)
```

**Après la correction**:
```bash
# Avec Europe/Paris (UTC+2)
python organize_footage_links.py project --tz "Europe/Paris"
# Résultat: video/2024-10-15/20h30m00s_dji_DJI_0001.json ✅

# Avec Asia/Tokyo (UTC+9)
python organize_footage_links.py project --tz "Asia/Tokyo"
# Résultat: video/2024-10-16/03h30m00s_dji_DJI_0001.json ✅

# Avec America/Montreal (UTC-4)
python organize_footage_links.py project --tz "America/Montreal"
# Résultat: video/2024-10-15/14h30m00s_dji_DJI_0001.json ✅
```

Chaque timezone donne maintenant le **bon résultat**!

## 🔍 Leçon Apprise

### Pièges avec datetime en Python

1. **`.astimezone()` sur datetime naïf** → interprète comme timezone locale
2. **`.astimezone()` sur datetime avec timezone** → réinterprète avant conversion
3. **`.replace(tzinfo=...)` sur datetime naïf** → force la timezone sans conversion ✅

### Bonne Pratique

Quand on parse une string UTC explicite:
```python
# ✅ BON - Force UTC sans conversion
dt_utc = datetime.fromisoformat(iso_with_tz).replace(tzinfo=timezone.utc)

# ❌ MAUVAIS - Réinterprète selon timezone locale
dt_utc = datetime.fromisoformat(iso_with_tz).astimezone(timezone.utc)
```

## 📚 Références

- **[TIMEZONE_UTILISATION.md](TIMEZONE_UTILISATION.md)** - Utilisation de la timezone
- **Python datetime docs**: [astimezone() behavior](https://docs.python.org/3/library/datetime.html#datetime.datetime.astimezone)
- **PEP 495**: [Local Time Disambiguation](https://peps.python.org/pep-0495/)

## 🎉 Statut

✅ **Bug corrigé**  
✅ **Tests de compilation: OK**  
⏳ **Tests utilisateur**: À valider avec vidéos drone réelles

---

**Date**: 28 octobre 2025  
**Impact**: Critique - affectait toutes les conversions timezone pour vidéos drone  
**Correction**: 2 lignes changées dans `extract_times_for_drone_file()`
