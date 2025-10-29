# Guide d'Utilisation - show_file_metadata.py

## 🎯 Vue d'Ensemble

`show_file_metadata.py` est un outil de débogage qui affiche **toutes** les métadonnées disponibles pour n'importe quel fichier vidéo ou photo. C'est l'outil idéal pour comprendre pourquoi un fichier n'est pas organisé correctement ou pour déboguer des problèmes de détection.

## 🚀 Méthodes d'Utilisation

### Méthode 1: Ligne de Commande (Recommandée)

```powershell
# Analyse basique d'un fichier
python debug\show_file_metadata.py "F:\MyProject\Footage_raw\drone\DJI_0001.mp4"

# Avec détection de source complète
python debug\show_file_metadata.py "F:\MyProject\Footage_raw\drone\DJI_0001.mp4" --footage-raw "F:\MyProject\Footage_raw"

# Sortie en JSON (pour automatisation)
python debug\show_file_metadata.py "video.mp4" --json

# Sauvegarder les métadonnées dans un fichier
python debug\show_file_metadata.py "video.mp4" --save
# Créera: video.mp4.metadata.txt

# Spécifier un timezone différent (pour fichiers drone)
python debug\show_file_metadata.py "DJI_0001.mp4" --tz "Europe/Paris"
```

### Méthode 2: Script Batch (Windows)

```powershell
# Utiliser le wrapper batch
SHOW_FILE_METADATA.BAT "F:\MyProject\video.mp4"

# Ou glisser-déposer le fichier sur SHOW_FILE_METADATA.BAT
```

### Méthode 3: Automatisation (Batch Processing)

```powershell
# PowerShell: Analyser tous les MP4 d'un dossier
Get-ChildItem "F:\Project\Footage_raw" -Recurse -Filter "*.mp4" | ForEach-Object {
    python debug\show_file_metadata.py $_.FullName --save
}

# CMD: Analyser tous les fichiers problématiques
for /r "F:\Project\Footage_raw\date_non_valide" %f in (*.*) do python debug\show_file_metadata.py "%f" --json >> analysis.json
```

## 📊 Exemples Concrets

### Exemple 1: Déboguer un fichier dans "date_non_valide"

**Problème:** Un fichier se retrouve dans `date_non_valide/` au lieu d'être classé par date.

```powershell
python debug\show_file_metadata.py "F:\Project\Footage_metadata_sorted\video\date_non_valide\00h00m00s_CELL-BLAIN_IMG_1234.txt"
```

**Analyser la sortie:**
```
🕐 EXTRACTION DE TIMESTAMPS
--------------------------------------------------------------------------------
FFprobe ISO       : ❌ Non trouvé
FFprobe source    : N/A
ExifTool datetime : ❌ Non trouvé
ExifTool status   : ⚠️ No QuickTime:DateTimeOriginal found
```

**Diagnostic:** Aucun timestamp trouvé → Fichier placé dans `date_non_valide` ✅ Correct

### Exemple 2: Vérifier la détection HDR/LOG

**Problème:** Un fichier D-Log de drone n'est pas détecté comme LOG.

```powershell
python debug\show_file_metadata.py "F:\Project\Footage_raw\drone\DJI_0001.mp4"
```

**Analyser la sortie:**
```
🎨 HDR/LOG DETECTION
Is Log/HDR        : YES - HDR/Log detected (transfer: smpte2084, colorspace: bt2020nc)
*** HDR TAG ***   : HDR/LOG
```

**Diagnostic:** Détection HDR/LOG correcte ✅

### Exemple 3: Comprendre la conversion timezone drone

**Problème:** Les timestamps des fichiers drone semblent incorrects.

```powershell
python debug\show_file_metadata.py "F:\Project\Footage_raw\drone\DJI_0001.mp4" --footage-raw "F:\Project\Footage_raw" --tz "America/Montreal"
```

**Analyser la sortie:**
```
🚁 TIMESTAMPS DRONE (Timezone: America/Montreal)
UTC ISO           : 2024-10-15T18:23:45+00:00
Local ISO         : 2024-10-15T14:23:45-04:00
Source tag        : format.tags.creation_time
Time diff (min)   : 0.0

⏰ TEMPS EXTRAIT (pour organisation)
Format HHhMMmSSs  : 14h23m45s
```

**Diagnostic:** 
- UTC: 18:23 (heure universelle)
- Local: 14:23 (Montreal -04:00)
- Le fichier sera nommé avec 14h23m45s ✅ Correct

### Exemple 4: Analyser un fichier iPhone

**Problème:** Les photos iPhone ont des dates incorrectes.

```powershell
python debug\show_file_metadata.py "F:\Project\Footage_raw\cell_john\IMG_1234.jpg"
```

**Analyser la sortie:**
```
🕐 EXTRACTION DE TIMESTAMPS
--------------------------------------------------------------------------------
FFprobe ISO       : ❌ Non trouvé
FFprobe source    : N/A
ExifTool datetime : 2024-10-15T14:30:00
ExifTool status   : ✅ SUCCESS (DateTimeOriginal fallback): 2024-10-15T14:30:00
```

**Diagnostic:** ExifTool a trouvé la date dans les métadonnées EXIF ✅

### Exemple 5: Comparer deux fichiers similaires

**Problème:** Deux fichiers similaires ont des comportements différents.

```powershell
# Sauvegarder les métadonnées des deux fichiers
python debug\show_file_metadata.py "file1.mp4" --json > file1.json
python debug\show_file_metadata.py "file2.mp4" --json > file2.json

# Comparer avec VS Code ou un outil de diff
code --diff file1.json file2.json
```

## 🎓 Comprendre la Sortie

### Section: 📁 INFORMATIONS FICHIER
- **Taille**: En bytes et MB
- **Dates**: Modification et création (filesystem)

### Section: 🔍 DÉTECTION DE TYPE
- **Chemin contient 'drone'**: Détermine si la conversion timezone s'applique
- **Chemin contient 'cell'**: Identifie les fichiers de téléphone
- **Date dans nom fichier**: Détecte les patterns YYYYMMDD, etc.

### Section: 📸 DÉTECTION DE SOURCE
- **Source Type**: Nom du sous-dossier dans Footage_raw
- **Source Tag**: Tag utilisé dans le nom de fichier organisé
- **Device Category**: Aerial/Mobile/Camera/etc.

### Section: 🕐 EXTRACTION DE TIMESTAMPS
- **FFprobe ISO**: Date extraite des métadonnées vidéo
- **ExifTool datetime**: Date extraite des métadonnées EXIF/QuickTime
- **Temps extrait**: Format utilisé dans le nom de fichier final

### Section: 🎬 MÉTADONNÉES VIDÉO TECHNIQUES
- **Résolution**: Largeur x Hauteur
- **Codec**: hevc, h264, prores, etc.
- **Color Space/Transfer/Primaries**: Pour détection HDR/LOG
- **Is Log/HDR**: Résultat de la détection automatique
- **HDR TAG**: Tag utilisé dans le CSV de métadonnées

### Section: 📊 DONNÉES BRUTES
- **FFprobe**: JSON complet avec tous les streams et format
- **ExifTool**: JSON complet avec toutes les métadonnées EXIF

## 🔧 Cas d'Usage Avancés

### Automatisation: Rapport de Projet

```powershell
# Créer un rapport complet pour tout le projet
$report = @()
Get-ChildItem "F:\Project\Footage_raw" -Recurse -Include "*.mp4","*.mov","*.jpg" | ForEach-Object {
    $meta = python debug\show_file_metadata.py $_.FullName --json | ConvertFrom-Json
    $report += [PSCustomObject]@{
        File = $_.Name
        Size_MB = [math]::Round($meta.file_info.size_mb, 2)
        Resolution = $meta.video_metadata.resolution
        HDR = $meta.video_metadata.hdr_tag
        Source = $meta.source_info.source_tag
    }
}
$report | Export-Csv "project_report.csv" -NoTypeInformation
```

### Validation: Vérifier la qualité des métadonnées

```powershell
# Trouver tous les fichiers sans timestamp valide
Get-ChildItem "F:\Project\Footage_raw" -Recurse -Filter "*.mp4" | ForEach-Object {
    $json = python debug\show_file_metadata.py $_.FullName --json | ConvertFrom-Json
    if ($null -eq $json.timestamps.extracted_time_for_organization) {
        Write-Host "⚠️  Pas de timestamp: $($_.Name)"
    }
}
```

### Documentation: Archiver les métadonnées

```powershell
# Sauvegarder toutes les métadonnées pour archivage
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveDir = "F:\Project\metadata_archive_$timestamp"
New-Item -ItemType Directory -Path $archiveDir

Get-ChildItem "F:\Project\Footage_raw" -Recurse -Include "*.mp4","*.mov" | ForEach-Object {
    $relativePath = $_.FullName.Replace("F:\Project\Footage_raw\", "")
    $outputPath = Join-Path $archiveDir "$relativePath.metadata.txt"
    $outputDir = Split-Path $outputPath -Parent
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    python debug\show_file_metadata.py $_.FullName > $outputPath
}
```

## 💡 Astuces

1. **Glisser-déposer**: Le plus simple pour analyser un fichier unique
2. **--json + PowerShell**: Idéal pour automatisation et filtrage
3. **--save**: Garde une trace des métadonnées à côté de chaque fichier
4. **--footage-raw**: Toujours utiliser pour obtenir la source correcte
5. **Redirection**: `> output.txt` pour sauvegarder la sortie complète

## 🐛 Résolution de Problèmes

### Le script ne trouve pas organize_footage_links.py
**Solution:** Le script ajoute automatiquement le chemin SORTING au sys.path. Assurez-vous que la structure de dossiers est intacte.

### "ffprobe not found"
**Solution:** Installez FFmpeg et ajoutez-le au PATH système.

### "exiftool not found"
**Solution:** Installez ExifTool depuis https://exiftool.org/ et ajoutez-le au PATH.

### La sortie JSON est trop grande
**Solution:** Utilisez `--json | Out-File -Encoding utf8 output.json` pour sauvegarder dans un fichier.

### Les caractères spéciaux s'affichent mal
**Solution:** PowerShell devrait utiliser UTF-8. Configurez avec: `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`

## 📚 Ressources

- **Documentation complète**: `debug/README.md`
- **Script principal**: `SORTING/organize_footage_links.py`
- **Wrapper batch**: `SHOW_FILE_METADATA.BAT`
