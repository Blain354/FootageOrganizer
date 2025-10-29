# Nouvel Outil: Visualiseur de Métadonnées Complet

## 📅 Date: 28 octobre 2025

## 🎯 Objectif

Créer un outil de débogage puissant pour afficher **toutes** les métadonnées disponibles d'un fichier vidéo ou photo, facilitant le diagnostic des problèmes d'organisation.

## ✨ Nouveaux Fichiers Créés

### 1. `debug/show_file_metadata.py` ⭐ (Script Principal)
**Fonctionnalités:**
- ✅ Affiche toutes les informations de fichier (taille, dates)
- ✅ Détection de type (drone, cell, date dans nom)
- ✅ Détection de source (avec --footage-raw)
- ✅ Extraction de timestamps (FFprobe, ExifTool, filename)
- ✅ Métadonnées vidéo complètes (codec, résolution, colorspace)
- ✅ Détection HDR/LOG automatique
- ✅ Données brutes FFprobe et ExifTool en JSON
- ✅ Conversion timezone pour fichiers drone
- ✅ Mode JSON pour automatisation
- ✅ Sauvegarde dans fichier .txt

**Usage:**
```bash
python debug\show_file_metadata.py "file.mp4"
python debug\show_file_metadata.py "file.mp4" --footage-raw "path\to\Footage_raw"
python debug\show_file_metadata.py "file.mp4" --json
python debug\show_file_metadata.py "file.mp4" --save
```

### 2. `SHOW_FILE_METADATA.BAT` (Wrapper Windows)
**Fonctionnalités:**
- ✅ Interface simplifiée pour Windows
- ✅ Support glisser-déposer
- ✅ Validation de Python et du script
- ✅ Messages d'erreur clairs
- ✅ Passage de tous les arguments au script Python

**Usage:**
```bash
SHOW_FILE_METADATA.BAT "file.mp4"
# Ou glisser-déposer le fichier sur le .BAT
```

### 3. `debug/README.md` (Documentation)
Documentation complète de l'outil avec:
- 📋 Exemples d'utilisation détaillés
- 📊 Exemple de sortie (texte et JSON)
- 🔧 Cas d'usage pratiques
- 💡 Conseils et astuces
- 🐛 Résolution de problèmes

### 4. `GUIDE_METADATA_VIEWER.md` (Guide Utilisateur)
Guide complet avec:
- 🎯 Vue d'ensemble
- 🚀 3 méthodes d'utilisation
- 📊 5 exemples concrets de débogage
- 🎓 Explication détaillée de chaque section
- 🔧 Cas d'usage avancés (automatisation, validation, archivage)
- 💡 Astuces pratiques
- 🐛 Résolution de problèmes

## 📝 Fichiers Modifiés

### `README.md`
**Ajouts:**
1. Section "Utility Scripts" mise à jour avec les nouveaux outils
2. Nouvelle sous-section "🔍 Debugging Tool: Show File Metadata" dans Troubleshooting
3. Exemples d'utilisation avec commandes
4. Liste des métadonnées affichées

## 🎓 Fonctions Utilisées

Le script réutilise les fonctions existantes de `organize_footage_links.py`:

```python
# Métadonnées vidéo
extract_video_metadata(path)

# Détection de source
detect_video_source_type(path, footage_raw_path)

# Timestamps
_ffprobe_creation_time(path)
_exiftool_quicktime_datetime(path)
_get_exiftool_datetime_unified(path)
extract_times_for_drone_file(path, tz_name)
extract_time_from_file(path, tz_name)

# Détection
_has_filename_datetime(path)
_path_has_drone_segment(path)
_path_has_cell_segment(path)
```

## 📊 Exemple de Sortie

### Mode Texte (par défaut)
```
================================================================================
MÉTADONNÉES COMPLÈTES: DJI_0001.mp4
================================================================================

📁 INFORMATIONS FICHIER
--------------------------------------------------------------------------------
Chemin complet    : F:\Project\Footage_raw\drone\DJI_0001.mp4
Nom               : DJI_0001.mp4
Taille            : 2,457,890,123 bytes (2343.45 MB)

🔍 DÉTECTION DE TYPE
--------------------------------------------------------------------------------
Chemin contient 'drone' : ✅ OUI
Date dans nom fichier   : ❌ NON

📸 DÉTECTION DE SOURCE
--------------------------------------------------------------------------------
Source Tag        : DRONE
Device Category   : Aerial

🕐 EXTRACTION DE TIMESTAMPS
--------------------------------------------------------------------------------
FFprobe ISO       : 2024-10-15T18:23:45.000000Z
ExifTool datetime : ❌ Non trouvé

🚁 TIMESTAMPS DRONE (Timezone: America/Montreal)
UTC ISO           : 2024-10-15T18:23:45+00:00
Local ISO         : 2024-10-15T14:23:45-04:00

⏰ TEMPS EXTRAIT (pour organisation)
Format HHhMMmSSs  : 14h23m45s

🎬 MÉTADONNÉES VIDÉO TECHNIQUES
--------------------------------------------------------------------------------
Résolution        : 3840x2160
Codec             : hevc
Color Space       : bt2020nc
*** HDR TAG ***   : HDR/LOG

📊 DONNÉES BRUTES FFPROBE
{...JSON complet...}
```

### Mode JSON (--json)
```json
{
  "file_info": {
    "path": "F:\\Project\\Footage_raw\\drone\\DJI_0001.mp4",
    "name": "DJI_0001.mp4",
    "size_mb": 2343.45
  },
  "detection": {
    "is_drone_path": true,
    "is_cell_path": false
  },
  "timestamps": {
    "ffprobe_iso": "2024-10-15T18:23:45.000000Z",
    "extracted_time_for_organization": "14h23m45s"
  },
  "video_metadata": {
    "resolution": "3840x2160",
    "codec": "hevc",
    "hdr_tag": "HDR/LOG"
  }
}
```

## 🎯 Cas d'Usage Principaux

### 1. Déboguer les problèmes d'organisation
```bash
# Fichier dans date_non_valide - pourquoi?
python debug\show_file_metadata.py "problem_file.mp4"
# → Vérifier la section "EXTRACTION DE TIMESTAMPS"
```

### 2. Vérifier la détection HDR/LOG
```bash
python debug\show_file_metadata.py "footage.mov"
# → Vérifier la section "HDR/LOG DETECTION"
```

### 3. Comprendre la conversion timezone
```bash
python debug\show_file_metadata.py "DJI_0001.mp4" --tz "Europe/Paris"
# → Vérifier la section "TIMESTAMPS DRONE"
```

### 4. Automatisation et rapports
```bash
# Générer un rapport JSON de tous les fichiers
Get-ChildItem *.mp4 | ForEach-Object {
    python debug\show_file_metadata.py $_.FullName --json
} | ConvertFrom-Json
```

### 5. Documentation et archivage
```bash
# Sauvegarder les métadonnées à côté de chaque fichier
python debug\show_file_metadata.py "video.mp4" --save
# → Crée video.mp4.metadata.txt
```

## ✅ Avantages

1. **Diagnostic Complet**: Toutes les métadonnées en un seul endroit
2. **Débogage Facile**: Comprendre rapidement pourquoi un fichier a un comportement spécifique
3. **Automatisation**: Mode JSON pour scripting et analyse en masse
4. **Documentation**: Mode --save pour archiver les métadonnées
5. **Simplicité**: Interface batch pour glisser-déposer
6. **Réutilisation**: Utilise les mêmes fonctions que le script principal
7. **Complet**: FFprobe + ExifTool + détections personnalisées

## 🔧 Intégration

Le nouvel outil s'intègre parfaitement dans le workflow existant:

```
1. Problème détecté lors de l'organisation
   ↓
2. Analyser avec show_file_metadata.py
   ↓
3. Identifier la cause (pas de timestamp, mauvais colorspace, etc.)
   ↓
4. Corriger le fichier source ou ajuster le script
   ↓
5. Réorganiser avec organize_footage_links.py
```

## 📚 Documentation Créée

1. **`debug/README.md`**: Documentation technique de l'outil
2. **`GUIDE_METADATA_VIEWER.md`**: Guide utilisateur complet avec exemples
3. **Commentaires dans le code**: Docstrings détaillées
4. **README.md principal**: Section troubleshooting mise à jour

## 🎉 Conclusion

Un outil complet de visualisation de métadonnées est maintenant disponible! Il permet de:
- ✅ Déboguer facilement les problèmes d'organisation
- ✅ Comprendre comment les métadonnées sont extraites
- ✅ Valider la détection HDR/LOG
- ✅ Vérifier les conversions timezone
- ✅ Automatiser l'analyse en masse
- ✅ Documenter les métadonnées de projet

**Usage rapide:**
```bash
# Méthode 1: Glisser-déposer sur SHOW_FILE_METADATA.BAT
# Méthode 2: python debug\show_file_metadata.py "file.mp4"
# Méthode 3: python debug\show_file_metadata.py "file.mp4" --json
```

Parfait pour répondre à la question: "Pourquoi ce fichier a-t-il ce comportement?"
