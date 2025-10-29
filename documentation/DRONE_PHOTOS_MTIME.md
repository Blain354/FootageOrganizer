# 📸 Photos de Drone - Utilisation du Mtime

## 📅 Date: 28 octobre 2025

## 🎯 Amélioration Apportée

Les **photos de drone** utilisent maintenant le **mtime** (modification time) du fichier pour extraire la date, avec application des ajustements temporels si configurés.

## 🔄 Comportement Précédent

### Vidéos de Drone
✅ Utilisaient les métadonnées QuickTime (via ffprobe)
✅ Gestion du timezone et conversion UTC → local
✅ Très fiable et précis

### Photos de Drone
❌ Tentaient d'utiliser ffprobe (ne fonctionne pas sur les photos)
❌ Fallback sur filename ou mtime, mais **sans ajustement temporel**
❌ Incohérent avec les vidéos du même groupe

## ✅ Nouveau Comportement

### Vidéos de Drone
✅ Inchangé: Métadonnées QuickTime avec ajustement
✅ Timezone gérée correctement
✅ Ajustement appliqué si configuré

### Photos de Drone
✅ **Utilisation du mtime directement**
✅ **Ajustement temporel appliqué si configuré**
✅ Cohérent avec les vidéos du même groupe
✅ Logging clair avec emoji 📸

## 🔧 Implémentation

### Fonction Ajoutée

```python
def _is_photo(p: Path) -> bool:
    """Check if file is a photo based on extension"""
    photo_extensions = PHOTO_EXT_DEFAULT.lower().split(',')
    return p.suffix.lower() in photo_extensions
```

Extensions photos détectées:
- `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`
- `.raw`, `.cr2`, `.cr3`, `.nef`, `.arw`, `.dng`
- `.heic`, `.heif`

### Logique Modifiée dans `file_date()`

**Avant**:
```python
if _path_has_drone_segment(p):
    drone_data = extract_times_for_drone_file(p, tz_name)
    # Fonctionne seulement pour vidéos
    # Photos ignorées et traitées comme fichiers normaux
```

**Après**:
```python
if _path_has_drone_segment(p):
    # Pour les VIDÉOS de drone
    if not _is_photo(p):
        drone_data = extract_times_for_drone_file(p, tz_name)
        if drone_data:
            # ... extraction QuickTime avec ajustement
    
    # Pour les PHOTOS de drone
    else:
        ts = p.stat().st_mtime
        dt = datetime.fromtimestamp(ts)
        logging.debug(f"📸 Using mtime for drone photo {p.name}: ...")
        # Apply adjustment if configured
        return apply_adjustment_and_return(dt)
```

## 📊 Exemple Concret

### Configuration
```json
{
    "dji_mini4": "+00000001_000000"
}
```

### Structure
```
Footage_raw/
  dji_mini4/
    DJI_0001.MP4   (vidéo, mtime: 2024-10-15 14:30:00)
    DJI_0002.JPG   (photo, mtime: 2024-10-15 14:35:00)
```

### Résultat

**Avant l'amélioration**:
```
Footage_metadata_sorted/
  video/
    2024-10-16/                    ← Vidéo ajustée (+1 jour)
      14h30m00s_dji_mini4_DJI_0001.json
  photo/
    2024-10-15/                    ← Photo NON ajustée ❌
      14h35m00s_dji_mini4_DJI_0002.json
```

**Après l'amélioration**:
```
Footage_metadata_sorted/
  video/
    2024-10-16/                    ← Vidéo ajustée (+1 jour)
      14h30m00s_dji_mini4_DJI_0001.json
  photo/
    2024-10-16/                    ← Photo AUSSI ajustée (+1 jour) ✅
      14h35m00s_dji_mini4_DJI_0002.json
```

**Résultat**: Photos et vidéos du même groupe dans le **même dossier de date**!

## 🧪 Tests Effectués

### Test 1: Photo Drone Sans Ajustement
```
Mtime: 2024-10-15 14:30:00
Ajustement: (aucun)
Résultat: 2024-10-15
Status: ✅ PASS
```

### Test 2: Photo Drone Avec +1 Jour
```
Mtime: 2024-10-15 14:30:00
Ajustement: +00000001_000000 (dji_mini4)
Résultat: 2024-10-16
Status: ✅ PASS (date correctement ajustée)
```

### Test 3: Groupe Non Configuré
```
Mtime: 2024-10-15 14:30:00
Groupe: other_camera (pas dans config)
Résultat: 2024-10-15
Status: ✅ PASS (pas d'ajustement appliqué)
```

### Test 4: Configuration Réelle
```
Groupes testés:
  - canon: 2024-10-16 (+1 jour) ✅
  - safari6d: 2024-10-15 (-2h, même jour) ✅
  - avata: 2024-10-15 (+2h, même jour) ✅
  - drone: 2024-10-15 (-2h, même jour) ✅
```

## 📝 Logs Générés

### Photo de Drone
```
DEBUG: 📸 Using mtime for drone photo DJI_0002.JPG: 2024-10-15 14:35:00
INFO: ⏰ Applied time adjustment to group 'dji_mini4': +00000001_000000
DEBUG:    Original: 2024-10-15 14:35:00
DEBUG:    Adjusted: 2024-10-16 14:35:00
```

### Vidéo de Drone (inchangé)
```
DEBUG: 📅 Extracted time from QuickTime for DJI_0001.MP4: 14:30:00
INFO: ⏰ Applied time adjustment to group 'dji_mini4': +00000001_000000
DEBUG:    Original: 2024-10-15 14:30:00
DEBUG:    Adjusted: 2024-10-16 14:30:00
```

## 🎯 Avantages

### ✅ Cohérence
Photos et vidéos du même groupe utilisent le même ajustement → même dossier de destination.

### ✅ Simplicité
Pas besoin de traiter les photos de drone différemment dans la configuration.

### ✅ Fiabilité
Mtime est disponible pour tous les fichiers, pas de dépendance sur métadonnées EXIF parfois absentes.

### ✅ Flexibilité
Ajustement par groupe permet de corriger les erreurs d'horloge spécifiques à chaque drone.

## ⚠️  Limitations

### Mtime vs Métadonnées
Le **mtime** peut être modifié lors de:
- Copie de fichiers (selon l'outil utilisé)
- Édition de fichiers
- Changement de système de fichiers

**Recommandation**: Transférer les fichiers depuis la carte SD du drone directement, sans édition intermédiaire.

### Timezone
Le mtime est dans le timezone local du système. Si les fichiers ont été copiés depuis un ordinateur dans un autre fuseau horaire, le mtime peut être décalé.

**Solution**: Utiliser l'ajustement temporel pour corriger ce décalage.

## 🔍 Détection

### Comment Détecter un Fichier Drone

La fonction `_path_has_drone_segment()` vérifie si le chemin contient:
- `drone`
- `dji`
- `avata`
- `mini4`

**Exemple**:
```
Footage_raw/dji_mini4/photo.jpg     ✅ Détecté comme drone
Footage_raw/drone/IMG_1234.JPG      ✅ Détecté comme drone
Footage_raw/avata/DJI_0001.MP4      ✅ Détecté comme drone
Footage_raw/camera/photo.jpg        ❌ Non détecté comme drone
```

### Comment Détecter une Photo

La fonction `_is_photo()` vérifie l'extension:
```python
.jpg, .jpeg, .png, .tiff, .tif
.raw, .cr2, .cr3, .nef, .arw, .dng
.heic, .heif
```

## 📚 Documentation Associée

- **[GUIDE_AJUSTEMENT_TEMPS.md](GUIDE_AJUSTEMENT_TEMPS.md)** - Guide d'utilisation des ajustements
- **[AJUSTEMENT_TEMPOREL_GROUPES.md](AJUSTEMENT_TEMPOREL_GROUPES.md)** - Architecture technique
- **[README.md](../README.md)** - Documentation principale

## 🎉 Conclusion

Les photos de drone bénéficient maintenant du **même système d'ajustement temporel** que les vidéos, assurant une **organisation cohérente** de tous les fichiers d'un même groupe.

**Résultat**: Workflow simplifié et organisation logique! 📸🚁

---

**Implémenté par**: GitHub Copilot  
**Date**: 28 octobre 2025  
**Tests**: ✅ Tous passés  
**Status**: Production Ready
