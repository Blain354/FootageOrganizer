#!/usr/bin/env python3
"""
show_file_metadata.py

Affiche toutes les métadonnées disponibles pour un fichier vidéo ou photo.

Utilise les mêmes fonctions que organize_footage_links.py pour extraire:
- Métadonnées vidéo (résolution, codec, colorspace, HDR/LOG)
- Timestamps (ffprobe, exiftool, filename, mtime)
- Informations de source (type, catégorie)
- Toutes les données brutes ffprobe et exiftool

Usage:
    python show_file_metadata.py FILE_PATH [--footage-raw FOOTAGE_RAW_PATH]

Arguments:
    FILE_PATH         : Chemin vers le fichier à analyser
    
Options:
    --footage-raw     : Chemin vers le dossier Footage_raw pour détection de source
    --tz              : Timezone pour conversion drone (défaut: America/Montreal)
    --json            : Sortie en format JSON
    --save            : Sauvegarder dans un fichier .txt à côté du fichier source

Exemples:
    python show_file_metadata.py "video.mp4"
    python show_file_metadata.py "F:\\Project\\Footage_raw\\drone\\DJI_0001.mp4" --footage-raw "F:\\Project\\Footage_raw"
    python show_file_metadata.py "photo.jpg" --json
    python show_file_metadata.py "video.mov" --save
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import logging

# Importer les fonctions du script principal
sys.path.insert(0, str(Path(__file__).parent.parent / "SORTING"))
from organize_footage_links import (
    extract_video_metadata,
    detect_video_source_type,
    _ffprobe_creation_time,
    _exiftool_quicktime_datetime,
    _get_exiftool_datetime_unified,
    _has_filename_datetime,
    _path_has_drone_segment,
    _path_has_cell_segment,
    extract_times_for_drone_file,
    extract_time_from_file
)

def get_raw_ffprobe_data(path: Path) -> dict:
    """Obtient toutes les données brutes de ffprobe"""
    try:
        cmd = ["ffprobe", "-v", "error", "-print_format", "json", 
               "-show_format", "-show_streams", str(path)]
        out = subprocess.check_output(cmd, text=True, timeout=30)
        return json.loads(out)
    except Exception as e:
        return {"error": str(e)}

def get_raw_exiftool_data(path: Path) -> dict:
    """Obtient toutes les données brutes d'exiftool"""
    try:
        cmd = ["exiftool", "-j", str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data[0] if data else {}
        return {"error": result.stderr}
    except FileNotFoundError:
        return {"error": "exiftool not installed"}
    except Exception as e:
        return {"error": str(e)}

def format_metadata_display(metadata: dict, path: Path, footage_raw_path: Path = None, tz_name: str = "America/Montreal") -> str:
    """Formate les métadonnées pour un affichage lisible"""
    output = []
    output.append("=" * 80)
    output.append(f"MÉTADONNÉES COMPLÈTES: {path.name}")
    output.append("=" * 80)
    output.append("")
    
    # Informations de base du fichier
    output.append("📁 INFORMATIONS FICHIER")
    output.append("-" * 80)
    output.append(f"Chemin complet    : {path}")
    output.append(f"Nom               : {path.name}")
    output.append(f"Extension         : {path.suffix}")
    if path.exists():
        stat = path.stat()
        output.append(f"Taille            : {stat.st_size:,} bytes ({stat.st_size / (1024**2):.2f} MB)")
        output.append(f"Date modification : {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"Date création     : {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        output.append("⚠️  Fichier n'existe pas!")
    output.append("")
    
    # Détection de type
    output.append("🔍 DÉTECTION DE TYPE")
    output.append("-" * 80)
    output.append(f"Chemin contient 'drone' : {'✅ OUI' if _path_has_drone_segment(path) else '❌ NON'}")
    output.append(f"Chemin contient 'cell'  : {'✅ OUI' if _path_has_cell_segment(path) else '❌ NON'}")
    output.append(f"Date dans nom fichier   : {'✅ OUI' if _has_filename_datetime(path) else '❌ NON'}")
    output.append("")
    
    # Source detection
    if footage_raw_path:
        output.append("📸 DÉTECTION DE SOURCE")
        output.append("-" * 80)
        source_info = detect_video_source_type(path, footage_raw_path)
        output.append(f"Source Type       : {source_info['source_type']}")
        output.append(f"Source Tag        : {source_info['source_tag']}")
        output.append(f"Device Category   : {source_info['device_category']}")
        output.append("")
    
    # Timestamps
    output.append("🕐 EXTRACTION DE TIMESTAMPS")
    output.append("-" * 80)
    
    # FFprobe creation time
    ffprobe_iso, ffprobe_src = _ffprobe_creation_time(path)
    output.append(f"FFprobe ISO       : {ffprobe_iso or '❌ Non trouvé'}")
    output.append(f"FFprobe source    : {ffprobe_src or 'N/A'}")
    
    # Exiftool datetime
    exiftool_dt, exiftool_msg = _get_exiftool_datetime_unified(path)
    output.append(f"ExifTool datetime : {exiftool_dt or '❌ Non trouvé'}")
    output.append(f"ExifTool status   : {exiftool_msg}")
    
    # Drone-specific times
    if _path_has_drone_segment(path):
        output.append(f"\n🚁 TIMESTAMPS DRONE (Timezone: {tz_name})")
        drone_data = extract_times_for_drone_file(path, tz_name)
        if drone_data:
            output.append(f"UTC ISO           : {drone_data['utc_iso']}")
            output.append(f"Local ISO         : {drone_data['local_iso']}")
            output.append(f"Source tag        : {drone_data['source_tag']}")
            output.append(f"Time diff (min)   : {drone_data['time_diff_minutes']:.1f}")
        else:
            output.append("❌ Pas de données drone trouvées")
    
    # Extracted time for organization
    extracted_time = extract_time_from_file(path, tz_name)
    output.append(f"\n⏰ TEMPS EXTRAIT (pour organisation)")
    output.append(f"Format HHhMMmSSs  : {extracted_time or '❌ Non extrait'}")
    output.append("")
    
    # Video metadata
    output.append("🎬 MÉTADONNÉES VIDÉO TECHNIQUES")
    output.append("-" * 80)
    video_meta = extract_video_metadata(path)
    if video_meta:
        output.append(f"Résolution        : {video_meta.get('resolution', 'N/A')}")
        output.append(f"Frame Rate        : {video_meta.get('frame_rate', 'N/A')}")
        output.append(f"Codec             : {video_meta.get('codec', 'N/A')}")
        output.append(f"Pixel Format      : {video_meta.get('pixel_format', 'N/A')}")
        output.append(f"Color Space       : {video_meta.get('color_space', 'N/A')}")
        output.append(f"Color Transfer    : {video_meta.get('color_transfer', 'N/A')}")
        output.append(f"Color Primaries   : {video_meta.get('color_primaries', 'N/A')}")
        output.append(f"Format            : {video_meta.get('format_name', 'N/A')}")
        output.append(f"Duration          : {video_meta.get('duration', 'N/A')} seconds")
        output.append(f"Bit Rate          : {video_meta.get('bit_rate', 'N/A')} bits/s")
        output.append(f"\n🎨 HDR/LOG DETECTION")
        output.append(f"Is Log/HDR        : {video_meta.get('is_log', 'N/A')}")
        output.append(f"*** HDR TAG ***   : {video_meta.get('hdr_tag', 'N/A')}")
    else:
        output.append("❌ Métadonnées vidéo non disponibles")
    output.append("")
    
    # Raw ffprobe data
    output.append("📊 DONNÉES BRUTES FFPROBE")
    output.append("-" * 80)
    raw_ffprobe = metadata.get('raw_ffprobe', {})
    if 'error' in raw_ffprobe:
        output.append(f"❌ Erreur: {raw_ffprobe['error']}")
    else:
        output.append(json.dumps(raw_ffprobe, indent=2, ensure_ascii=False))
    output.append("")
    
    # Raw exiftool data
    output.append("📊 DONNÉES BRUTES EXIFTOOL")
    output.append("-" * 80)
    raw_exiftool = metadata.get('raw_exiftool', {})
    if 'error' in raw_exiftool:
        output.append(f"⚠️  {raw_exiftool['error']}")
    else:
        output.append(json.dumps(raw_exiftool, indent=2, ensure_ascii=False))
    output.append("")
    
    output.append("=" * 80)
    return "\n".join(output)

def collect_all_metadata(path: Path, footage_raw_path: Path = None, tz_name: str = "America/Montreal") -> dict:
    """Collecte toutes les métadonnées disponibles"""
    metadata = {
        'file_info': {
            'path': str(path),
            'name': path.name,
            'extension': path.suffix,
            'exists': path.exists()
        }
    }
    
    if path.exists():
        stat = path.stat()
        metadata['file_info'].update({
            'size_bytes': stat.st_size,
            'size_mb': stat.st_size / (1024**2),
            'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'ctime': datetime.fromtimestamp(stat.st_ctime).isoformat()
        })
    
    # Detection
    metadata['detection'] = {
        'is_drone_path': _path_has_drone_segment(path),
        'is_cell_path': _path_has_cell_segment(path),
        'has_filename_datetime': _has_filename_datetime(path)
    }
    
    # Source
    if footage_raw_path:
        metadata['source_info'] = detect_video_source_type(path, footage_raw_path)
    
    # Timestamps
    ffprobe_iso, ffprobe_src = _ffprobe_creation_time(path)
    exiftool_dt, exiftool_msg = _get_exiftool_datetime_unified(path)
    
    metadata['timestamps'] = {
        'ffprobe_iso': ffprobe_iso,
        'ffprobe_source': ffprobe_src,
        'exiftool_datetime': exiftool_dt,
        'exiftool_status': exiftool_msg,
        'extracted_time_for_organization': extract_time_from_file(path, tz_name)
    }
    
    # Drone times
    if _path_has_drone_segment(path):
        drone_data = extract_times_for_drone_file(path, tz_name)
        if drone_data:
            metadata['drone_times'] = drone_data
    
    # Video metadata
    metadata['video_metadata'] = extract_video_metadata(path)
    
    # Raw data
    metadata['raw_ffprobe'] = get_raw_ffprobe_data(path)
    metadata['raw_exiftool'] = get_raw_exiftool_data(path)
    
    return metadata

def main():
    parser = argparse.ArgumentParser(
        description="Affiche toutes les métadonnées disponibles pour un fichier vidéo ou photo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python show_file_metadata.py "video.mp4"
  python show_file_metadata.py "F:\\Project\\Footage_raw\\drone\\DJI_0001.mp4" --footage-raw "F:\\Project\\Footage_raw"
  python show_file_metadata.py "photo.jpg" --json
  python show_file_metadata.py "video.mov" --save
        """
    )
    
    parser.add_argument("file_path", type=Path, help="Chemin vers le fichier à analyser")
    parser.add_argument("--footage-raw", type=Path, help="Chemin vers Footage_raw pour détection de source")
    parser.add_argument("--tz", default="America/Montreal", help="Timezone pour conversion drone")
    parser.add_argument("--json", action="store_true", help="Sortie en format JSON")
    parser.add_argument("--save", action="store_true", help="Sauvegarder dans un fichier .txt")
    
    args = parser.parse_args()
    
    # Valider le fichier
    file_path = args.file_path.resolve()
    if not file_path.exists():
        print(f"❌ Erreur: Le fichier n'existe pas: {file_path}")
        sys.exit(1)
    
    # Collecter les métadonnées
    print(f"🔍 Analyse en cours de: {file_path.name}")
    metadata = collect_all_metadata(file_path, args.footage_raw, args.tz)
    
    # Affichage
    if args.json:
        output = json.dumps(metadata, indent=2, ensure_ascii=False, default=str)
        print(output)
    else:
        output = format_metadata_display(metadata, file_path, args.footage_raw, args.tz)
        print(output)
    
    # Sauvegarde
    if args.save:
        output_file = file_path.with_suffix(file_path.suffix + '.metadata.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            if args.json:
                f.write(json.dumps(metadata, indent=2, ensure_ascii=False, default=str))
            else:
                f.write(format_metadata_display(metadata, file_path, args.footage_raw, args.tz))
        print(f"\n✅ Métadonnées sauvegardées dans: {output_file}")

if __name__ == "__main__":
    main()
