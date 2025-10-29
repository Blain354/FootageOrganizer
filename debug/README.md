# Debug Tools - Utilitaires de Débogage

## 📋 show_file_metadata.py

Utilitaire pour afficher toutes les métadonnées complètes d'un fichier vidéo ou photo.

### 🎯 Fonctionnalités

- **Informations fichier**: Taille, dates, chemin complet
- **Détection de type**: Drone, cell, date dans le nom
- **Source detection**: Type, tag, catégorie d'appareil
- **Timestamps**: FFprobe, ExifTool, extraction drone, temps pour organisation
- **Métadonnées vidéo**: Résolution, codec, colorspace, HDR/LOG
- **Données brutes**: FFprobe et ExifTool complets en JSON

### 📥 Utilisation

#### Usage Basique
```bash
# Analyser un fichier
python debug\show_file_metadata.py "path\to\video.mp4"

# Analyser avec détection de source
python debug\show_file_metadata.py "F:\Project\Footage_raw\drone\DJI_0001.mp4" --footage-raw "F:\Project\Footage_raw"

# Sortie en JSON
python debug\show_file_metadata.py "video.mp4" --json

# Sauvegarder les métadonnées dans un fichier
python debug\show_file_metadata.py "video.mp4" --save
```

#### Options Disponibles
```
Arguments:
  file_path              Chemin vers le fichier à analyser (requis)

Options:
  --footage-raw PATH     Chemin vers Footage_raw pour détection de source
  --tz TIMEZONE          Timezone pour conversion drone (défaut: America/Montreal)
  --json                 Sortie en format JSON
  --save                 Sauvegarder dans un fichier .txt à côté du fichier source
```

### 📊 Exemple de Sortie

#### Mode Texte (par défaut)
```
================================================================================
MÉTADONNÉES COMPLÈTES: DJI_0001.mp4
================================================================================

📁 INFORMATIONS FICHIER
--------------------------------------------------------------------------------
# Debug Tools - Debugging Utilities

## 📋 show_file_metadata.py

Utility to display full metadata for a video or photo file.

### 🎯 Features

- File information: size, timestamps, full path
- Type detection: drone, phone, date-in-filename detection
- Source detection: source tag and device category
- Timestamps: FFprobe, ExifTool, drone extraction, organization time
- Video metadata: resolution, codec, colorspace, HDR/LOG detection
- Raw data: full FFprobe and ExifTool JSON outputs

### 📥 Usage

#### Basic usage
```bash
# Analyze a single file
python debug\show_file_metadata.py "path\to\video.mp4"

# Analyze with footage-raw detection
python debug\show_file_metadata.py "F:\Project\Footage_raw\drone\DJI_0001.mp4" --footage-raw "F:\Project\Footage_raw"

# JSON output
python debug\show_file_metadata.py "video.mp4" --json

# Save metadata to a file
python debug\show_file_metadata.py "video.mp4" --save
```

#### Available options
```
Arguments:
  file_path              Path to the file to analyze (required)

Options:
  --footage-raw PATH     Path to Footage_raw for source detection
  --tz TIMEZONE          Timezone for drone conversion (default: America/Montreal)
  --json                 Output JSON
  --save                 Save metadata to a .txt file next to the source file
```

### 📊 Example output

#### Text mode (default)
```
================================================================================
FULL METADATA: DJI_0001.mp4
================================================================================

FILE INFORMATION
--------------------------------------------------------------------------------
Full path         : F:\Project\Footage_raw\drone\DJI_0001.mp4
Name              : DJI_0001.mp4
Extension         : .mp4
Size              : 2,457,890,123 bytes (2343.45 MB)
Modified time     : 2024-10-15 14:23:45
Creation time     : 2024-10-15 14:23:45

TYPE DETECTION
--------------------------------------------------------------------------------
Path contains 'drone' : ✅ YES
Path contains 'cell'  : ❌ NO
Date in filename      : ❌ NO

SOURCE DETECTION
--------------------------------------------------------------------------------
Source Type        : drone
Source Tag         : DRONE
Device Category    : Aerial

TIMESTAMP EXTRACTION
--------------------------------------------------------------------------------
FFprobe ISO        : 2024-10-15T18:23:45.000000Z
FFprobe source     : format.tags.creation_time

ExifTool datetime  : ❌ Not found
ExifTool status    : ⚠️ No QuickTime:DateTimeOriginal found

DRONE TIMESTAMPS (Timezone: America/Montreal)
UTC ISO            : 2024-10-15T18:23:45+00:00
Local ISO          : 2024-10-15T14:23:45-04:00
Source tag         : format.tags.creation_time
Time diff (min)    : 0.0

EXTRACTED TIME (for organization)
--------------------------------------------------------------------------------
Format HHhMMmSSs   : 14h23m45s

VIDEO TECHNICAL METADATA
--------------------------------------------------------------------------------
Resolution         : 3840x2160
Frame Rate         : 29.97 fps
Codec              : hevc
Pixel Format       : yuv420p10le
Color Space        : bt2020nc
Color Transfer     : smpte2084
Color Primaries    : bt2020
Format             : mov,mp4,m4a,3gp,3g2,mj2
Duration           : 125.45 seconds
Bit Rate           : 100234567 bits/s

HDR/LOG DETECTION
Is Log/HDR         : YES - HDR/Log detected (transfer: smpte2084, colorspace: bt2020nc, primaries: bt2020, 10+ bit: yuv420p10le)
*** HDR TAG ***    : HDR/LOG

RAW FFPROBE DATA
--------------------------------------------------------------------------------
{
  "streams": [...],
  "format": {...}
}

RAW EXIFTOOL DATA
--------------------------------------------------------------------------------
{
  "SourceFile": "DJI_0001.mp4",
  "FileType": "MP4",
  ...
}
```

#### JSON mode (--json)
```json
{
  "file_info": {
    "path": "F:\\Project\\Footage_raw\\drone\\DJI_0001.mp4",
    "name": "DJI_0001.mp4",
    "extension": ".mp4",
    "exists": true,
    "size_bytes": 2457890123,
    "size_mb": 2343.45,
    "mtime": "2024-10-15T14:23:45",
    "ctime": "2024-10-15T14:23:45"
  },
  "detection": {
    "is_drone_path": true,
    "is_cell_path": false,
    "has_filename_datetime": false
  },
  "source_info": {
    "source_type": "drone",
    "source_tag": "DRONE",
    "device_category": "Aerial"
  },
  "timestamps": {
    "ffprobe_iso": "2024-10-15T18:23:45.000000Z",
    "ffprobe_source": "format.tags.creation_time",
    "exiftool_datetime": null,
    "exiftool_status": "⚠️ No QuickTime:DateTimeOriginal found",
    "extracted_time_for_organization": "14h23m45s"
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
  "raw_ffprobe": {...},
  "raw_exiftool": {...}
}
```

### 🔧 Use cases

#### 1. Debug a date problem
```bash
# See why a file ended up with the wrong date
python debug\show_file_metadata.py "problematic_file.mp4"
```

#### 2. Check HDR/LOG detection
```bash
# Understand why a file wasn't detected as LOG
python debug\show_file_metadata.py "footage.mov" --json | findstr "hdr_tag"
```

#### 3. Inspect drone timestamps
```bash
# See how timestamps are converted for a drone file
python debug\show_file_metadata.py "F:\Project\Footage_raw\drone\DJI_0001.mp4" --footage-raw "F:\Project\Footage_raw" --tz "Europe/Paris"
```

#### 4. Document a project's metadata
```bash
# Save metadata for all MP4 files under a folder
for /r "F:\Project\Footage_raw" %f in (*.mp4) do python debug\show_file_metadata.py "%f" --save
```

#### 5. Compare multiple files
```bash
# JSON output for automated comparison
python debug\show_file_metadata.py "file1.mp4" --json > file1_meta.json
python debug\show_file_metadata.py "file2.mp4" --json > file2_meta.json
# Compare with your preferred diff tool
```

### 🛠️ Dependencies

Uses the same dependencies as the main scripts:
- **Python 3.8+**
- **ffprobe** (ffmpeg) - for video metadata
- **exiftool** (optional) - for photo/QuickTime metadata

### 💡 Tips

- Use `--footage-raw` for correct source detection
- `--json` is great for automation and parsing
- `--save` writes a `.metadata.txt` file next to the analyzed file
- FFprobe/ExifTool raw outputs contain ALL available metadata

### 🐛 Common debugging notes

**"exiftool not installed"**
- ExifTool is not installed or not on PATH
- Download from: https://exiftool.org/

**"ffprobe error"**
- FFmpeg/FFprobe not installed or not on PATH
- Download from: https://ffmpeg.org/

**"Import could not be resolved"**
- Linting warning only; the script works at runtime
- The script adds the SORTING path to sys.path dynamically

### 📚 See also

- `metadata_inspector.py` - older debugging helper (similar)
- `organize_footage_links.py` - main organization script
- `create_metadata.py` - generates CSV with grouped metadata
