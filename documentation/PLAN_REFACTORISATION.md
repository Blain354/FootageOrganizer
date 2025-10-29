# 🔧 Plan de Refactorisation - organize_footage_links.py

## 📅 Date: 28 octobre 2025

## 🎯 Objectif

Simplifier et clarifier le code pour:
- Attribution de groupe basée UNIQUEMENT sur le dossier parent
- Liste explicite des drones en constante
- Logique simple et claire
- Réduire la complexité

## 📊 État Actuel (Problèmes)

### Problème 1: Détection de Groupe Ambiguë

**Code actuel**: Le groupe est détecté de plusieurs façons:
- Par le dossier parent
- Par des patterns dans le nom de fichier (DJI_, IMG_, etc.)
- Par détection de métadonnées

**Résultat**: Un fichier `DJI_0001.MP4` dans `Footage_raw/avata/` peut être détecté comme "dji" ou "avata" selon la fonction.

### Problème 2: Détection Drone Dispersée

**Code actuel**: Plusieurs endroits vérifient si c'est un drone:
- `_path_has_drone_segment()` - vérifie le chemin
- `detect_video_source_type()` - vérifie nom/metadata
- Logique dans `file_date()` - conditions imbriquées

### Problème 3: Logique Complexe dans file_date()

**Code actuel**: ~150 lignes avec de nombreuses branches if/else imbriquées

## ✅ Solution Proposée

### 1. Constantes Globales (EN HAUT DU FICHIER)

```python
# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Drone folders - Only these folders use UTC conversion
DRONE_FOLDERS = [
    "drone",
    "dji",
    "mini4",
    "mavic"
]

# Photo extensions
PHOTO_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".raw", ".cr2", ".nef", 
    ".arw", ".dng", ".heic", ".heif", ".webp", ".tiff"
]
```

### 2. Fonctions de Détection Simplifiées

```python
def get_group_from_path(file_path: Path, footage_raw_root: Path) -> str:
    """
    Get group ONLY from folder structure.
    
    Example:
        Footage_raw/avata/DJI_0001.MP4 → "avata"
        Footage_raw/canon/IMG_001.jpg → "canon"
    """
    try:
        rel = file_path.relative_to(footage_raw_root)
        if rel.parent == Path("."):
            return "root"
        return rel.parts[0].lower()
    except ValueError:
        return file_path.parent.name.lower() or "root"


def is_drone_group(group_name: str) -> bool:
    """Check if group is in DRONE_FOLDERS list"""
    return group_name.lower() in DRONE_FOLDERS


def is_photo(file_path: Path) -> bool:
    """Check if file extension is in PHOTO_EXTENSIONS"""
    return file_path.suffix.lower() in PHOTO_EXTENSIONS
```

### 3. Logique Simplifiée dans file_date()

```python
def file_date_simple(file_path: Path, footage_raw_root: Path, tz_name: str, time_adjustments: dict):
    """
    Extract date with CLEAR logic:
    
    1. Get group from folder
    2. Extract datetime based on file type:
       - Drone video → QuickTime UTC + conversion
       - Photo (any) → mtime
       - Other → filename/exiftool/mtime
    3. Apply time adjustment for group
    4. Return date
    """
    
    # STEP 1: Get group
    group = get_group_from_path(file_path, footage_raw_root)
    
    # STEP 2: Extract datetime
    is_drone = is_drone_group(group)
    is_photo_file = is_photo(file_path)
    
    if is_drone and not is_photo_file:
        # Drone VIDEO: UTC conversion
        dt = extract_drone_video_time(file_path, tz_name)
    elif is_photo_file:
        # ALL photos: mtime
        dt = datetime.fromtimestamp(file_path.stat().st_mtime)
    else:
        # Other: standard extraction
        dt = extract_standard_time(file_path)
    
    # Fallback
    if dt is None:
        dt = datetime.fromtimestamp(file_path.stat().st_mtime)
    
    # STEP 3: Apply adjustment
    if time_adjustments and group in time_adjustments:
        dt = apply_time_delta(dt, time_adjustments[group])
    
    # STEP 4: Return date
    return dt.date()
```

## 📋 Changements Requis

### Fichiers à Modifier

1. **organize_footage_links.py**:
   - ✅ Ajouter DRONE_FOLDERS en haut
   - ✅ Ajouter PHOTO_EXTENSIONS en haut
   - ✅ Créer get_group_from_path()
   - ✅ Créer is_drone_group()
   - ✅ Créer is_photo()
   - ⏳ Refactoriser file_date()
   - ⏳ Simplifier extract_times_for_drone_file()
   - ⏳ Nettoyer detect_video_source_type()

2. **main() loop**:
   - Passer footage_raw_root à file_date()
   - Utiliser group retourné par get_group_from_path()

### Avantages

✅ **Simplicité**: Logique claire en 3 étapes  
✅ **Prévisibilité**: Group = dossier, toujours  
✅ **Maintenabilité**: Facile d'ajouter un drone (juste modifier la liste)  
✅ **Débogage**: Facile de suivre le flux  
✅ **Performance**: Moins de conditions imbriquées

## 🎯 Résultat Attendu

### Exemple: DJI_0001.MP4 dans avata/

**Ancien comportement** (confus):
```
1. file_date() appelée
2. _path_has_drone_segment() → False (avata pas dans la liste)
3. Utilise logique standard
4. detect_video_source_type() détecte "DJI" → tag "dji"
5. Ajustement cherche "dji" dans config → PAS TROUVÉ
6. Pas d'ajustement appliqué ❌
```

**Nouveau comportement** (clair):
```
1. get_group_from_path() → "avata"
2. is_drone_group("avata") → False
3. Utilise mtime (ou metadata standard)
4. Ajustement cherche "avata" dans config → TROUVÉ
5. Ajustement appliqué ✅
```

## ⚙️ Configuration

### specific_group_time_adjust.json

```json
{
    "avata": "+00000000_060000",
    "canon": "+00000001_000000",
    "safari6d": "-00000000_040000",
    "dji": "+00000000_020000"
}
```

**Logique**: 
- `avata/` dossier → groupe "avata" → ajustement +6h
- `dji/` dossier → groupe "dji" → drone + ajustement +2h
- `canon/` dossier → groupe "canon" → ajustement +1 jour

## 🔍 Tests Recommandés

### Test 1: Fichier Avata
```
Fichier: Footage_raw/avata/DJI_0001.MP4
Groupe attendu: "avata"
Drone: Non
Extraction: mtime
Ajustement: +6h
```

### Test 2: Fichier DJI Drone
```
Fichier: Footage_raw/dji/video.MP4
Groupe attendu: "dji"
Drone: Oui
Extraction: QuickTime UTC + conversion
Ajustement: +2h
```

### Test 3: Photo Canon
```
Fichier: Footage_raw/canon/IMG_001.jpg
Groupe attendu: "canon"
Drone: Non  
Extraction: mtime
Ajustement: +1 jour
```

## 📚 Documentation Liée

- **[GUIDE_AJUSTEMENT_TEMPS.md](GUIDE_AJUSTEMENT_TEMPS.md)** - Utilisation ajustements
- **[POURQUOI_AJUSTEMENT_NE_CHANGE_PAS.md](POURQUOI_AJUSTEMENT_NE_CHANGE_PAS.md)** - Problème fichiers existants

## ⏰ Statut

- ✅ Constantes définies
- ✅ Nouvelles fonctions créées
- ⏳ **EN COURS**: Refactor complet nécessaire
- ⏳ Tests à écrire après refactor

---

**Date**: 28 octobre 2025  
**Status**: Plan créé, refactor partiel en cours  
**Recommandation**: Refactor complet dans une branche séparée pour éviter de casser la version actuelle
