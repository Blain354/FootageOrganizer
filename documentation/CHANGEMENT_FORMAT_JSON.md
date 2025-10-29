# Changement Majeur: Format JSON pour les Placeholders

## 📅 Date: 28 octobre 2025

## 🎯 Objectif

Remplacer les fichiers placeholders .txt par des fichiers .json structurés, permettant:
1. **Meilleur parsing**: Format standardisé et facile à analyser
2. **Métadonnées brutes incluses**: FFprobe et ExifTool complets pour debugging direct
3. **Structure claire**: Données organisées hiérarchiquement
4. **Beautiful JSON**: Formatage avec indent=4 pour lisibilité humaine

## 🔄 Changements Effectués

### 1. organize_footage_links.py - Génération de Placeholders JSON

#### Fonctions Ajoutées
```python
def get_raw_ffprobe_metadata(path: Path) -> dict:
    """Obtient toutes les données brutes de ffprobe en format JSON"""
    
def get_raw_exiftool_metadata(path: Path) -> dict:
    """Obtient toutes les données brutes d'exiftool en format JSON"""
```

#### Fonction Modifiée: `copy_file()`
**Avant**: Créait un fichier `.txt` avec format texte libre  
**Après**: Crée un fichier `.json` avec structure standardisée

**Structure JSON Créée**:
```json
{
    "placeholder_info": {
        "created_at": "2025-10-28T14:30:00",
        "original_filename": "DJI_0001.mp4",
        "original_path": "F:\\Project\\Footage_raw\\drone\\DJI_0001.mp4",
        "original_size_bytes": 123456789,
        "placeholder_format_version": "1.0"
    },
    "file_info": {
        "name": "DJI_0001.mp4",
        "extension": ".mp4",
        "size_bytes": 123456789,
        "size_mb": 117.74,
        "mtime": "2024-10-15T14:23:45",
        "mtime_readable": "2024-10-15 14:23:45"
    },
    "source_detection": {
        "source_type": "drone",
        "source_tag": "DRONE",
        "device_category": "Aerial",
        "is_drone_path": true,
        "is_cell_path": false
    },
    "timestamps": {
        "filename_time": null,
        "exiftool": {
            "datetime": null,
            "status": "⚠️ No QuickTime:DateTimeOriginal found"
        },
        "drone": {
            "utc_iso": "2024-10-15T18:23:45+00:00",
            "local_iso": "2024-10-15T14:23:45-04:00",
            "source_tag": "format.tags.creation_time",
            "time_diff_minutes": 0.0,
            "decision_info": "Time difference: 0.0 minutes from mtime"
        }
    },
    "video_metadata": {
        "resolution": "3840x2160",
        "frame_rate": "29.97 fps",
        "codec": "hevc",
        "pixel_format": "yuv420p10le",
        "color_space": "bt2020nc",
        "color_transfer": "smpte2084",
        "color_primaries": "bt2020",
        "is_log": "YES - HDR/Log detected (...)",
        "hdr_tag": "HDR/LOG",
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "duration": "125.45",
        "bit_rate": "100234567"
    },
    "raw_metadata": {
        "ffprobe": {
            "streams": [...],
            "format": {...}
        },
        "exiftool": {
            "SourceFile": "...",
            "FileType": "MP4",
            ...
        }
    }
}
```

### 2. transfer_organized_footage.py - Support Dual Format

#### Fonction Modifiée: `extract_original_path_from_txt()` → `extract_original_path_from_placeholder()`
```python
def extract_original_path_from_placeholder(placeholder_file: Path) -> Optional[Path]:
    """
    Extrait le chemin depuis .txt OU .json
    Rétrocompatibilité complète
    """
```

#### Fonction Modifiée: `update_txt_file_path()` → `update_placeholder_file_path()`
```python
def update_placeholder_file_path(placeholder_file: Path, new_video_path: Path):
    """
    Met à jour le chemin dans .txt OU .json
    Pour JSON, ajoute une section transfer_info
    """
```

**Section transfer_info ajoutée au JSON après transfert**:
```json
{
    ...
    "transfer_info": {
        "transferred_at": "2025-10-28T15:30:00",
        "new_location": "F:\\Project\\Footage\\video\\2024-10-15\\14h23m45s_DRONE_DJI_0001.mp4"
    }
}
```

#### Fonction Modifiée: `find_txt_files()` → `find_placeholder_files()`
```python
def find_placeholder_files(organized_dir: Path) -> List[Path]:
    """
    Trouve à la fois les .json ET les .txt
    Supporte les deux formats simultanément
    """
```

### 3. create_metadata.py - Support Dual Format

#### Fonction Modifiée: `parse_txt_metadata()` → `parse_placeholder_metadata()`
```python
def parse_placeholder_metadata(placeholder_file_path: Path) -> Tuple[str, str, str, str]:
    """
    Parse .txt OU .json selon l'extension
    Retourne (source_tag, hdr_tag, original_filename, new_path)
    """
```

#### Fonction Modifiée: `find_video_files()`
- Recherche maintenant à la fois `*.json` et `*.txt`
- Exclut les fichiers dans dossiers `photo/` et `photos/`
- Support transparent des deux formats

### 4. Suppression: metadata_inspector.py

**Raison**: Redondant avec `show_file_metadata.py` qui est bien meilleur
- ✅ `show_file_metadata.py` utilise les fonctions du script principal
- ✅ Intégration avec la détection de source
- ✅ Meilleure structure et documentation
- ✅ Support de timezone pour drones

## ✨ Avantages du Format JSON

### 1. **Lisibilité Humaine**
```json
{
    "video_metadata": {
        "resolution": "3840x2160",
        "hdr_tag": "HDR/LOG"
    }
}
```
vs ancien TXT:
```
Resolution: 3840x2160
*** HDR TAG: HDR/LOG ***
```

### 2. **Parsing Programmatique**
```python
# JSON - Simple et fiable
with open(file, 'r') as f:
    data = json.load(f)
    source = data['source_detection']['source_tag']
    hdr = data['video_metadata']['hdr_tag']

# TXT - Regex et parsing complexe
content = f.read()
source_match = re.search(r'\*\*\* SOURCE TAG: ([^\*]+) \*\*\*', content)
if source_match:
    source = source_match.group(1).strip()
```

### 3. **Métadonnées Brutes pour Debugging**
Le JSON inclut `raw_metadata` avec:
- **Toutes** les données ffprobe (streams complets)
- **Toutes** les données exiftool (EXIF complet)

**Usage**:
```python
# Ouvrir le placeholder dans l'arborescence organisée
with open("video/2024-10-15/14h23m45s_DRONE_DJI_0001.json") as f:
    data = json.load(f)
    
# Accéder aux métadonnées brutes directement
raw_ffprobe = data['raw_metadata']['ffprobe']
raw_exiftool = data['raw_metadata']['exiftool']

# Analyser directement sans réexécuter ffprobe/exiftool
print(raw_ffprobe['streams'][0]['codec_name'])
```

### 4. **Extensibilité**
Facile d'ajouter de nouveaux champs:
```json
{
    ...
    "stabilization_info": {
        "is_stabilized": true,
        "gyroflow_version": "1.5.0"
    }
}
```

### 5. **Validation**
Structure standard permet validation automatique:
```python
import json
import jsonschema

# Valider la structure
with open("placeholder.json") as f:
    data = json.load(f)
    jsonschema.validate(data, schema)
```

## 🔙 Rétrocompatibilité

### Support des Anciens Fichiers .txt

Tous les scripts supportent **les deux formats simultanément**:

```python
# transfer_organized_footage.py trouve les deux
placeholder_files = find_placeholder_files(organized_dir)
# Résultat: [*.json, *.txt]

# Extraction fonctionne pour les deux
path = extract_original_path_from_placeholder(file)
# Fonctionne que file soit .json OU .txt

# Mise à jour adaptée au format
update_placeholder_file_path(file, new_path)
# JSON → ajoute transfer_info
# TXT → ajoute section TRANSFER INFO
```

### Migration Douce

1. **Nouveaux fichiers**: Créés en JSON (.json)
2. **Anciens fichiers**: Continuent de fonctionner (.txt)
3. **Pas de conversion nécessaire**: Support transparent

## 📊 Comparaison Format

### Taille des Fichiers

**TXT typique**: ~2-3 KB  
**JSON avec raw_metadata**: ~15-25 KB

**Impact**: Légèrement plus gros, mais:
- ✅ Métadonnées complètes incluses
- ✅ Pas besoin de réexécuter ffprobe/exiftool
- ✅ Debugging direct dans l'arborescence organisée
- ✅ Toujours des placeholders légers vs fichiers vidéo (GB)

### Performance

**Parsing TXT**: Regex multiples, parsing ligne par ligne  
**Parsing JSON**: `json.load()` - Optimal en Python

**Résultat**: JSON plus rapide à parser! ⚡

## 🎯 Use Cases Améliorés

### 1. Debugging Direct dans l'Arborescence
```powershell
# Ouvrir n'importe quel JSON dans l'arborescence
code "Footage_metadata_sorted/video/2024-10-15/14h23m45s_DRONE_DJI_0001.json"

# Voir immédiatement:
# - Toutes les métadonnées vidéo
# - Détection de source
# - Timestamps extraits
# - Raw ffprobe complet
# - Raw exiftool complet
```

### 2. Scripts d'Analyse Automatisés
```python
import json
from pathlib import Path

# Analyser tous les placeholders
for json_file in Path("Footage_metadata_sorted").rglob("*.json"):
    with open(json_file) as f:
        data = json.load(f)
        
    # Extraire facilement ce qu'on veut
    if data['video_metadata']['hdr_tag'] == 'HDR/LOG':
        print(f"LOG file: {data['file_info']['name']}")
        print(f"  Codec: {data['video_metadata']['codec']}")
        print(f"  Color space: {data['video_metadata']['color_space']}")
```

### 3. Validation de Qualité
```python
# Vérifier que tous les fichiers ont des métadonnées valides
for json_file in Path("Footage_metadata_sorted").rglob("*.json"):
    with open(json_file) as f:
        data = json.load(f)
    
    # Vérifier présence de métadonnées critiques
    assert data['source_detection']['source_tag'] != 'UNKNOWN'
    assert data['video_metadata'] is not None
    assert 'raw_metadata' in data
```

## 📝 Documentation Mise à Jour

- ✅ Docstrings mis à jour dans tous les scripts
- ✅ README principal mentionne le nouveau format
- ✅ Commentaires dans le code expliquent la rétrocompatibilité
- ✅ Ce fichier documente la transition complète

## 🎉 Conclusion

Le passage au format JSON pour les placeholders apporte:
- ✅ **Meilleure structure**: Données organisées hiérarchiquement
- ✅ **Debugging intégré**: Métadonnées brutes incluses directement
- ✅ **Parsing simplifié**: JSON natif vs regex complexes
- ✅ **Extensibilité**: Facile d'ajouter de nouveaux champs
- ✅ **Rétrocompatibilité**: Support complet des anciens .txt
- ✅ **Beautiful format**: indent=4 pour lisibilité humaine

**Format**: `14h23m45s_DRONE_DJI_0001.json` au lieu de `.txt`  
**Contenu**: Structure JSON complète avec raw_metadata pour debugging direct  
**Taille**: ~20 KB vs 2 KB (négligeable vs fichiers vidéo de GB)  
**Bénéfice**: **Debugging direct dans l'arborescence organisée!** 🎯
