#!/usr/bin/env python3
"""
create_metadata.py

Generates CSV file with video metadata for organization and color grading in DaVinci Resolve.

Functions:
- Analyzes .txt placeholder files in Footage_metadata_sorted/
- Extracts video metadata (source, colorspace, LOG/HDR profiles)
- Automatically determines groups according to detection rules
- Assigns unique colors per group (colorblind-compatible palette)
- Generates metadata.csv for use with TagFootageByCSV.py

Usage:
    python create_metadata.py PROJECT_ROOT [OPTIONS]

Arguments:
    PROJECT_ROOT : Project root folder (must contain Footage_metadata_sorted/)
    
Options:
    --dry-run : Display summary without writing CSV file

Expected structure:
    PROJECT_ROOT/
    ├── Footage_metadata_sorted/  (folder with .txt placeholders)
    └── Footage/                  (destination folder for metadata.csv)

Output:
    metadata.csv in PROJECT_ROOT/Footage/ with columns:
    filename, relpath, group_name, clip_color, color_space, source

Automatic detection:
- Color profiles: S-Log3, D-Log, HLG, Rec709, CineLikeD, GoProFlat
- Logical groups based on codec and colorspace
- Distinct color assignment to avoid confusion
"""

import argparse
import csv
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Couleurs valides (ordonnées pour éviter confusion daltonisme rouge-vert)
VALID_COLORS = [
    "Blue",      # Très distinct pour daltoniens
    "Green",     # Préféré pour DJI LOG
    "Purple",    # Très distinct
    "Cyan",      # Distinct du rouge/vert
    "Yellow",    # Distinct mais attention avec fond blanc
    "Orange",    # Peut être confondu avec rouge
    "Pink",      # Distinct
    "Fuchsia",   # Magenta variant
    "Violet",    # Purple variant
    "Teal",      # Cyan variant
    "Lavender",  # Purple variant
    "Rose",      # Pink variant
    "Magenta",   # Similar to fuchsia
    "Brown",     # Neutral
    "Olive",     # Green variant - attention daltonisme
    "Tan",       # Brown variant
    "Sand",      # Neutral
    "Red",       # À éviter pour daltonisme mais gardé en fin
]

# Couleurs par famille de sources (couleurs similaires par source)
SOURCE_COLOR_FAMILIES = {
    "DRONE": ["Green", "Olive"],           # Types de vert pour DJI
    "CELL-BLAIN": ["Orange", "Tan"],           # Types d'orange pour Blain
    "CANON": ["Blue", "Cyan"],                 # Types de bleu pour Canon
}

# Couleurs disponibles pour l'attribution dynamique (excluant celles déjà utilisées dans les familles)
DYNAMIC_COLORS = [
    "Purple", "Violet",        # Purple family
    "Pink", "Rose", "Fuchsia", # Pink family  
    "Yellow", "Sand",          # Yellow family
    "Brown", "Lavender",       # Neutral colors
    "Teal", "Magenta",         # Remaining colors
    "Red"                      # Last resort (daltonisme)
]

def setup_logging():
    """Configure le logging minimal"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

def parse_txt_metadata(txt_file_path: Path) -> Tuple[str, str, str, str]:
    """
    Parse les métadonnées depuis un fichier .txt placeholder
    
    Returns:
        (source_tag, hdr_tag, original_filename, new_path)
    """
    source_tag = "UNKNOWN"
    hdr_tag = "SDR"
    original_filename = ""
    new_path = ""
    
    try:
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraire le SOURCE TAG
        source_match = re.search(r'\*\*\* SOURCE TAG: ([^\*]+) \*\*\*', content)
        if source_match:
            source_tag = source_match.group(1).strip()
        
        # Extraire le HDR TAG
        hdr_match = re.search(r'\*\*\* HDR TAG: ([^\*]+) \*\*\*', content)
        if hdr_match:
            hdr_tag = hdr_match.group(1).strip()
        
        # Extraire le nom original du fichier
        placeholder_match = re.search(r'PLACEHOLDER FOR: (.+)', content)
        if placeholder_match:
            original_filename = placeholder_match.group(1).strip()
        
        # Extraire le nouveau chemin (si transféré)
        new_location_match = re.search(r'New location: (.+)', content)
        if new_location_match:
            new_path = new_location_match.group(1).strip()
        else:
            # Si pas de nouvelle location, extraire le chemin original
            original_path_match = re.search(r'Original path: (.+)', content)
            if original_path_match:
                new_path = original_path_match.group(1).strip()
    
    except Exception as e:
        logging.warning(f"Erreur lecture métadonnées {txt_file_path}: {e}")
    
    return source_tag, hdr_tag, original_filename, new_path

def detect_source_and_encoding(filename: str, relpath: str) -> Tuple[str, str, str]:
    """
    OBSOLÈTE: Remplacé par parse_txt_metadata pour l'analyse des fichiers .txt
    Gardé pour compatibilité avec les fichiers .mp4 directs
    """
    """
    Détermine le groupe, color_space et source basé sur le nom de fichier et chemin
    
    Returns:
        (group_name, color_space, source)
    """
    filename_lower = filename.lower()
    relpath_lower = relpath.lower()
    
    # Détection de la source basée sur le chemin et nom de fichier
    source = ""
    base_group = ""
    
    # Règle 1: DJI Drone (priorité au chemin puis au nom de fichier)
    if any(indicator in relpath_lower for indicator in ["drone", "dji"]) or \
       any(indicator in filename_lower for indicator in ["dji_", "dji "]):
        source = "DJI_DRONE"
        base_group = "DJI"
    
    # Règle 2: Cell phones (vérifier dans l'ordre de priorité)
    elif "cell_blain" in relpath_lower:
        source = "CELL_BLAIN"
        base_group = "CELL_BLAIN"
    elif "cell_jo" in relpath_lower:
        source = "CELL_JO"
        base_group = "CELL_JO"
    elif "cell_waltz" in relpath_lower:
        source = "CELL_WALTZ"
        base_group = "CELL_WALTZ"
    elif "cell" in relpath_lower:
        # Cell générique si pas plus spécifique
        source = "CELL_PHONE"
        base_group = "CELL"
    
    # Règle 3: GoPro
    elif any(indicator in relpath_lower for indicator in ["gopro", "hero"]) or \
         any(indicator in filename_lower for indicator in ["gopro", "hero", "gp"]):
        source = "GOPRO"
        base_group = "GOPRO"
    
    # Règle 4: Camera générique
    elif any(indicator in relpath_lower for indicator in ["camera", "cam"]) or \
         any(indicator in filename_lower for indicator in ["dsc", "img", "mov"]):
        source = "CAMERA"
        base_group = "CAMERA"
    
    # Si aucune source détectée
    if not source:
        return "no_group", "Rec709", ""
    
    # Détection de l'encodage couleur
    color_space = "Rec709"  # Défaut
    encoding_suffix = "709"
    
    # Recherche d'indicateurs LOG/HDR dans le nom de fichier ou chemin
    log_indicators = ["log", "hdr", "hlg", "pq", "bt2020", "rec2020", "10bit"]
    if any(indicator in filename_lower for indicator in log_indicators) or \
       any(indicator in relpath_lower for indicator in log_indicators):
        color_space = "Log"
        encoding_suffix = "LOG"
    
    # Construire le nom du groupe final
    group_name = f"{base_group}_{encoding_suffix}"
    
    return group_name, color_space, source

def find_video_files(root_path: Path) -> List[Tuple[str, str, str, str, str]]:
    """
    Trouve tous les fichiers vidéo dans le dossier racine
    Analyse les .txt de métadonnées ou directement les .mp4
    
    Returns:
        Liste de tuples (filename, relpath, source_tag, hdr_tag, group_name)
    """
    video_files = []
    seen_relpaths = set()
    
    # D'abord chercher les fichiers .txt de métadonnées (exclure ceux dans dossier photos)
    all_txt_files = list(root_path.rglob("*.txt"))
    txt_files = [f for f in all_txt_files if "photos" not in f.parts]
    
    if all_txt_files:
        excluded_count = len(all_txt_files) - len(txt_files)
        excluded_files = [f for f in all_txt_files if "photos" in f.parts]
        logging.info(f"Mode métadonnées: analyse de {len(txt_files)} fichiers .txt (exclus {excluded_count} photos)")
        if excluded_files:
            logging.info(f"Photos exclues: {[f.name for f in excluded_files]}")
    
    if txt_files:
        for txt_file in txt_files:
            source_tag, hdr_tag, original_filename, video_path = parse_txt_metadata(txt_file)
            
            if not original_filename:
                continue
                
            # Utiliser le chemin du fichier vidéo (.mp4) comme relpath
            if video_path and Path(video_path).exists():
                try:
                    # Chemin relatif du fichier .mp4 depuis la racine avec des slashes "/"
                    relpath = Path(video_path).relative_to(root_path).as_posix()
                except ValueError:
                    # Si le fichier vidéo n'est pas sous root_path, essayer de construire le relpath
                    # en utilisant la structure du .txt mais avec extension .mp4
                    txt_relpath = txt_file.relative_to(root_path).as_posix()
                    relpath = txt_relpath.replace('.txt', '.mp4')
            else:
                # Fallback: construire le relpath basé sur le .txt mais avec extension .mp4
                txt_relpath = txt_file.relative_to(root_path).as_posix()
                relpath = txt_relpath.replace('.txt', '.mp4')
            
            # Ignorer les doublons
            if relpath in seen_relpaths:
                continue
            seen_relpaths.add(relpath)
            
            # Créer le nom du groupe basé sur source et encoding
            color_space = "Log" if hdr_tag == "HDR/LOG" else "Rec709"
            encoding_suffix = "LOG" if hdr_tag == "HDR/LOG" else "709"
            group_name = f"{source_tag}_{encoding_suffix}"
            
            # Le filename est maintenant le nom du fichier organisé (pas l'original)
            converted_filename = Path(relpath).name
            
            video_files.append((converted_filename, relpath, source_tag, color_space, group_name))
    
    else:
        # Mode fallback: analyser directement les fichiers .mp4
        logging.info("Mode fallback: analyse directe des fichiers .mp4")
        
        for file_path in root_path.rglob("*.mp4"):
            if file_path.is_file():
                filename = file_path.name
                relpath = file_path.relative_to(root_path).as_posix()
                
                if relpath in seen_relpaths:
                    continue
                seen_relpaths.add(relpath)
                
                # Utiliser l'ancienne méthode de détection
                group_name, color_space, source = detect_source_and_encoding_fallback(filename, relpath)
                source_tag = source if source else "UNKNOWN"
                
                video_files.append((filename, relpath, source_tag, color_space, group_name))
    
    return video_files

def detect_source_and_encoding_fallback(filename: str, relpath: str) -> Tuple[str, str, str]:
    """
    Détection fallback pour les fichiers .mp4 sans métadonnées .txt
    """
    filename_lower = filename.lower()
    relpath_lower = relpath.lower()
    
    # Détection de la source basée sur le chemin et nom de fichier
    source = ""
    base_group = ""
    
    # Règle 1: DJI Drone
    if any(indicator in relpath_lower for indicator in ["drone", "dji"]) or \
       any(indicator in filename_lower for indicator in ["dji_", "dji "]):
        source = "DJI-DRONE"
        base_group = "DJI-DRONE"
    
    # Règle 2: Cell phones
    elif "cell_blain" in relpath_lower:
        source = "CELL-BLAIN"
        base_group = "CELL-BLAIN"
    elif "cell_jo" in relpath_lower:
        source = "CELL-JO"
        base_group = "CELL-JO"
    elif "cell_waltz" in relpath_lower:
        source = "CELL-WALTZ"
        base_group = "CELL-WALTZ"
    elif "cell" in relpath_lower:
        source = "CELL-PHONE"
        base_group = "CELL-PHONE"
    
    # Règle 3: GoPro
    elif any(indicator in relpath_lower for indicator in ["gopro", "hero"]) or \
         any(indicator in filename_lower for indicator in ["gopro", "hero", "gp"]):
        source = "GOPRO"
        base_group = "GOPRO"
    
    # Règle 4: Camera générique
    elif any(indicator in relpath_lower for indicator in ["camera", "cam"]) or \
         any(indicator in filename_lower for indicator in ["dsc", "img", "mov"]):
        source = "CAMERA"
        base_group = "CAMERA"
    
    # Si aucune source détectée
    if not source:
        return "no_group", "Rec709", "UNKNOWN"
    
    # Détection de l'encodage couleur
    color_space = "Rec709"  # Défaut
    encoding_suffix = "709"
    
    # Recherche d'indicateurs LOG/HDR dans le nom de fichier ou chemin
    log_indicators = ["log", "hdr", "hlg", "pq", "bt2020", "rec2020", "10bit"]
    if any(indicator in filename_lower for indicator in log_indicators) or \
       any(indicator in relpath_lower for indicator in log_indicators):
        color_space = "Log"
        encoding_suffix = "LOG"
    
    # Construire le nom du groupe final
    group_name = f"{base_group}_{encoding_suffix}"
    
    return group_name, color_space, source

def assign_colors_to_groups(groups: set) -> Dict[str, str]:
    """
    Assigne des couleurs aux groupes de manière dynamique
    - Sources connues (DJI, CELL-BLAIN, CANON) utilisent leurs familles de couleurs
    - Nouvelles sources reçoivent des couleurs dynamiquement avec familles similaires
    """
    color_assignment = {}
    used_colors = set()
    
    # Grouper par source
    sources_groups = {}
    for group in groups:
        if '_' in group:
            source = group.rsplit('_', 1)[0]  # Tout sauf le dernier segment après _
        else:
            source = group
        
        if source not in sources_groups:
            sources_groups[source] = []
        sources_groups[source].append(group)
    
    # Pool de couleurs dynamiques disponibles
    dynamic_pool = DYNAMIC_COLORS.copy()
    
    # Traiter d'abord les sources avec familles prédéfinies
    for source, source_groups in sources_groups.items():
        if source in SOURCE_COLOR_FAMILIES:
            colors = SOURCE_COLOR_FAMILIES[source]
            
            # Assigner les couleurs dans l'ordre (généralement LOG puis 709)
            for i, group in enumerate(sorted(source_groups)):
                if i < len(colors):
                    color = colors[i]
                    if color not in used_colors:
                        color_assignment[group] = color
                        used_colors.add(color)
                        # Retirer la couleur du pool dynamique si elle y était
                        if color in dynamic_pool:
                            dynamic_pool.remove(color)
    
    # Traiter les sources inconnues avec attribution dynamique
    remaining_sources = [s for s in sources_groups.keys() if s not in SOURCE_COLOR_FAMILIES]
    
    for source in remaining_sources:
        source_groups_list = sources_groups[source]
        
        # Prendre les 2 prochaines couleurs du pool pour cette source
        colors_for_source = []
        if len(dynamic_pool) >= 2:
            colors_for_source = dynamic_pool[:2]
            dynamic_pool = dynamic_pool[2:]
        elif len(dynamic_pool) == 1:
            colors_for_source = [dynamic_pool[0]]
            dynamic_pool = []
        else:
            # Plus de couleurs disponibles, réutiliser depuis le début
            colors_for_source = ["Purple", "Violet"]
        
        # Assigner aux groupes de cette source
        for i, group in enumerate(sorted(source_groups_list)):
            if i < len(colors_for_source):
                color = colors_for_source[i]
                if color not in used_colors:
                    color_assignment[group] = color
                    used_colors.add(color)
                else:
                    # Trouver une couleur alternative
                    for alt_color in VALID_COLORS:
                        if alt_color not in used_colors:
                            color_assignment[group] = alt_color
                            used_colors.add(alt_color)
                            break
            else:
                # Plus de couleurs pour cette source, utiliser des alternatives
                for alt_color in VALID_COLORS:
                    if alt_color not in used_colors:
                        color_assignment[group] = alt_color
                        used_colors.add(alt_color)
                        break
    
    # Vérifier que tous les groupes ont une couleur
    for group in groups:
        if group not in color_assignment:
            for alt_color in VALID_COLORS:
                if alt_color not in used_colors:
                    color_assignment[group] = alt_color
                    used_colors.add(alt_color)
                    break
            else:
                # Dernier recours
                color_assignment[group] = "Sand"
    
    return color_assignment

def parse_txt_placeholder(txt_file: Path) -> Optional[dict]:
    """
    Parse un fichier .txt placeholder et extrait les métadonnées
    
    Retourne un dictionnaire avec:
    - original_filename: nom du fichier original
    - original_path: chemin complet original
    - source_tag: tag de la source
    - color_space: espace colorimétrique
    - is_log: si c'est du LOG/HDR
    - relpath: chemin relatif du .txt
    """
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraire le nom du fichier original
        original_filename = None
        for line in content.split('\n'):
            if line.startswith("PLACEHOLDER FOR: "):
                original_filename = line.replace("PLACEHOLDER FOR: ", "").strip()
                break
        
        # Extraire le chemin original
        original_path = None
        for line in content.split('\n'):
            if line.startswith("Original path: "):
                original_path = line.replace("Original path: ", "").strip()
                break
        
        # Extraire le source tag
        source_tag = None
        for line in content.split('\n'):
            if "*** SOURCE TAG: " in line:
                source_tag = line.replace("*** SOURCE TAG: ", "").replace(" ***", "").strip()
                break
        
        # Extraire le HDR tag pour déterminer le type d'encodage
        hdr_tag = None
        for line in content.split('\n'):
            if "*** HDR TAG: " in line:
                hdr_tag = line.replace("*** HDR TAG: ", "").replace(" ***", "").strip()
                break
        
        # Extraire le color space
        color_space = "Unknown"
        for line in content.split('\n'):
            if line.startswith("Color Space: "):
                color_space = line.replace("Color Space: ", "").strip()
                break
        
        # Extraire si c'est LOG/HDR
        is_log = False
        for line in content.split('\n'):
            if line.startswith("Is Log/HDR: "):
                is_log_str = line.replace("Is Log/HDR: ", "").strip()
                is_log = is_log_str.lower().startswith('yes') or 'log' in is_log_str.lower() or 'hdr' in is_log_str.lower()
                break
        
        if not original_filename or not source_tag:
            logging.warning(f"Métadonnées incomplètes dans {txt_file}")
            return None
        
        # Utiliser le nom renommé (basé sur le .txt) au lieu du nom original
        # Le nom .txt sans extension + l'extension du fichier original
        renamed_stem = txt_file.stem  # Nom du fichier .txt sans extension
        original_suffix = Path(original_filename).suffix  # Extension du fichier original
        expected_video_name = renamed_stem + original_suffix
        
        return {
            'original_filename': original_filename,
            'original_path': original_path,
            'source_tag': source_tag,
            'hdr_tag': hdr_tag,
            'color_space': color_space,
            'is_log': is_log,
            'txt_relpath': str(txt_file.relative_to(txt_file.parents[len(txt_file.parts)-2])) if len(txt_file.parts) > 1 else txt_file.name,
            'expected_video_name': expected_video_name  # Nom renommé attendu du fichier vidéo final
        }
        
    except Exception as e:
        logging.error(f"Erreur lecture {txt_file}: {e}")
        return None


def create_metadata_csv_from_txt(metadata_sorted_path: Path, project_root: Path, dry_run: bool = False) -> None:
    """
    Crée le fichier metadata.csv en lisant les fichiers .txt placeholders (vidéos seulement)
    """
    logging.info(f"Scan du dossier de métadonnées: {metadata_sorted_path}")
    
    # Trouver tous les fichiers .txt (exclure les photos)
    all_txt_files = []
    txt_files = []
    for txt_file in metadata_sorted_path.rglob("*.txt"):
        if txt_file.is_file():
            all_txt_files.append(txt_file)
            if "photos" not in txt_file.parts:
                txt_files.append(txt_file)
    
    if not txt_files and not all_txt_files:
        logging.warning("Aucun fichier .txt placeholder trouvé")
        return
        
    excluded_count = len(all_txt_files) - len(txt_files)
    logging.info(f"Trouvé {len(txt_files)} fichiers .txt vidéo (exclus {excluded_count} photos)")
    
    if not txt_files:
        logging.info("Aucun fichier vidéo trouvé après exclusion des photos")
        return
    
    # Analyser chaque fichier .txt
    metadata_rows = []
    groups_found = set()
    
    for txt_file in txt_files:
        parsed_data = parse_txt_placeholder(txt_file)
        if not parsed_data:
            continue
        
        # Utiliser directement le source tag du fichier .txt
        source_tag = parsed_data['source_tag']
        
        # Créer le nom de groupe basé sur la source et le type d'encodage
        base_group = source_tag
        
        # Utiliser le HDR TAG si disponible, sinon fallback sur is_log
        if parsed_data['hdr_tag']:
            hdr_tag = parsed_data['hdr_tag']
            if 'HDR' in hdr_tag or 'LOG' in hdr_tag:
                group_name = f"{base_group}_LOG"
            else:  # SDR
                group_name = f"{base_group}_709"
        else:
            # Fallback sur is_log
            if parsed_data['is_log']:
                group_name = f"{base_group}_LOG"
            else:
                group_name = f"{base_group}_709"
        
        groups_found.add(group_name)
        
        # Calculer le chemin relatif dans le dossier Footage final
        # Remplacer .txt par l'extension originale
        relative_txt_path = txt_file.relative_to(metadata_sorted_path)
        relative_video_path = relative_txt_path.with_suffix(Path(parsed_data['original_filename']).suffix)
        
        metadata_rows.append({
            'filename': parsed_data['expected_video_name'],
            'relpath': str(relative_video_path).replace('\\', '/'),  # Normalize path separators
            'group_name': group_name,
            'color_space': parsed_data['color_space'],
            'source': parsed_data['source_tag']
        })
    
    # Trier par relpath
    metadata_rows.sort(key=lambda x: x['relpath'])
    
    # Assigner les couleurs aux groupes
    color_assignment = assign_colors_to_groups(groups_found)
    
    # Ajouter les couleurs aux rows
    for row in metadata_rows:
        row['clip_color'] = color_assignment[row['group_name']]
    
    # Logs du résumé
    logging.info(f"Groupes créés: {len(groups_found)}")
    for group in sorted(groups_found):
        color = color_assignment[group]
        count = sum(1 for row in metadata_rows if row['group_name'] == group)
        logging.info(f"  {group}: {count} fichiers → {color}")
    
    # Déterminer où écrire le CSV
    footage_dir = project_root / "Footage"
    csv_path = footage_dir / "metadata.csv"
    
    if dry_run:
        logging.info("Mode dry-run: aucun fichier CSV écrit")
        logging.info(f"Le fichier serait créé à: {csv_path}")
        logging.info(f"Nombre total d'entrées: {len(metadata_rows)}")
        return
    
    # Créer le dossier Footage s'il n'existe pas
    footage_dir.mkdir(exist_ok=True)
    
    # Écrire le CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filename', 'relpath', 'group_name', 'clip_color', 'color_space', 'source']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
        
        # Écrire l'en-tête
        writer.writeheader()
        
        # Écrire les données
        for row in metadata_rows:
            writer.writerow(row)
    
    logging.info(f"✅ CSV créé avec succès: {csv_path}")
    logging.info(f"📊 {len(metadata_rows)} entrées écrites")


def create_metadata_csv(root_path: Path, dry_run: bool = False) -> None:
    """
    Crée le fichier metadata.csv avec toutes les informations
    """
    # Trouver tous les fichiers vidéo (via .txt ou directement .mp4)
    logging.info(f"Scan du dossier: {root_path}")
    video_files = find_video_files(root_path)
    
    if not video_files:
        logging.warning("Aucun fichier vidéo trouvé")
        return
    
    logging.info(f"Trouvé {len(video_files)} fichiers vidéo")
    
    # Analyser chaque fichier et collecter les groupes
    metadata_rows = []
    groups_found = set()
    
    for filename, relpath, source_tag, color_space, group_name in video_files:
        groups_found.add(group_name)
        
        metadata_rows.append({
            'filename': filename,
            'relpath': relpath,
            'group_name': group_name,
            'color_space': color_space,
            'source': source_tag
        })
    
    # Trier par relpath
    metadata_rows.sort(key=lambda x: x['relpath'])
    
    # Assigner les couleurs aux groupes
    color_assignment = assign_colors_to_groups(groups_found)
    
    # Ajouter les couleurs aux rows
    for row in metadata_rows:
        row['clip_color'] = color_assignment[row['group_name']]
    
    # Logs du résumé
    logging.info(f"Groupes créés: {len(groups_found)}")
    for group in sorted(groups_found):
        color = color_assignment[group]
        count = sum(1 for row in metadata_rows if row['group_name'] == group)
        logging.info(f"  {group}: {count} fichiers → {color}")
    
    if dry_run:
        # Calculer le chemin du CSV pour le dry-run
        footage_dir = root_path.parent / "Footage"
        csv_path = footage_dir / "metadata.csv"
        logging.info("Mode dry-run: aucun fichier CSV écrit")
        logging.info(f"Le fichier serait créé à: {csv_path}")
        return
    
    # Écrire le CSV dans le dossier "Footage" au même niveau que l'input
    footage_dir = root_path.parent / "Footage"
    footage_dir.mkdir(exist_ok=True)  # Créer le dossier s'il n'existe pas
    csv_path = footage_dir / "metadata.csv"
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filename', 'relpath', 'group_name', 'clip_color', 'color_space', 'source']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
        
        # Écrire l'en-tête
        writer.writeheader()
        
        # Écrire les données
        for row in metadata_rows:
            writer.writerow(row)
    
    logging.info(f"Fichier CSV créé: {csv_path}")
    logging.info(f"Lignes écrites: {len(metadata_rows)}")

def main():
    parser = argparse.ArgumentParser(description="Génère un fichier metadata.csv pour les fichiers vidéo basé sur les .txt placeholders")
    parser.add_argument("project_root", type=Path, 
                       help="Dossier racine du projet (doit contenir Footage_metadata_sorted/)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Affiche un résumé sans écrire le fichier CSV")
    
    args = parser.parse_args()
    
    setup_logging()
    
    project_root = args.project_root.resolve()
    metadata_sorted_path = project_root / "Footage_metadata_sorted"
    
    # Validation de la structure du projet
    if not project_root.exists():
        logging.error(f"Le dossier racine du projet n'existe pas: {project_root}")
        return
    
    if not metadata_sorted_path.exists():
        logging.error(f"Le dossier Footage_metadata_sorted n'existe pas: {metadata_sorted_path}")
        logging.error(f"Structure attendue: {project_root}/Footage_metadata_sorted/")
        return
    
    if not metadata_sorted_path.is_dir():
        logging.error(f"Footage_metadata_sorted n'est pas un dossier: {metadata_sorted_path}")
        return
    
    # Créer le metadata CSV basé sur les fichiers .txt
    create_metadata_csv_from_txt(metadata_sorted_path, project_root, args.dry_run)

if __name__ == "__main__":
    main()
