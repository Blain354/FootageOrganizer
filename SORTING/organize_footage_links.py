
#!/usr/bin/env python3
"""
organize_footage_links.py

Organizes video files by date creating secure .txt placeholders.

Functions:
- Recursively scans source folder for video files
- Organizes files in a type-based structure with dated folders
- Structure: photo/YYYY-MM-DD/ and video/YYYY-MM-DD/
- Creates .txt placeholder files containing metadata instead of moving files
- Names placeholders: {SOURCE}_{FILENAME}.txt where SOURCE is parent folder

Operation mode:
- Creates only lightweight .txt files containing original file information
- Automatically analyzes video metadata (codec, resolution, colorspace)
- Detects timezone and converts timestamps for drone files
- No original video files are moved or modified

Usage:
    python organize_footage_links.py INPUT_DIR OUTPUT_DIR [OPTIONS]

Arguments:
    INPUT_DIR   : Source folder containing video files
    OUTPUT_DIR  : Destination folder for placeholders
    
Options:
    --ext       : File extensions (.mp4,.mov,.avi,etc.)
    --tz        : Timezone for drone timestamp conversion (default: America/Montreal)
    --simulate  : Dry-run mode without writing files
    --list-tz   : List available timezones

Security:
- No original files are modified or moved
- Lightweight .txt placeholders for rapid prototyping
- Vérifications d'intégrité et logging complet
Security:
- No original files are modified or moved
- Lightweight .txt placeholders for rapid prototyping
- Integrity checks and comprehensive logging
"""
from typing import Union, Optional
import argparse
import os
import sys
import shutil
import subprocess
import re
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import zoneinfo
from typing import Tuple

# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Drone folder names that require special UTC timestamp conversion
# Only folders with these exact names (case-insensitive) will use QuickTime metadata
DRONE_FOLDERS = [
    "drone",
    "dji", 
    "mini4",
    "mavic"
]

# Photo file extensions (case-insensitive)
PHOTO_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", 
    ".raw", ".cr2", ".nef", ".arw", ".dng",
    ".heic", ".heif", ".webp", ".tiff", ".tif"
]

# ============================================================================
# ANSI COLORS FOR LOGGING
# ============================================================================

# ANSI color codes for console output
class LogColors:
    """ANSI color codes for colored console output"""
    BLUE = '\033[94m'      # Light blue for INFO
    CYAN = '\033[96m'      # Cyan for DEBUG
    YELLOW = '\033[93m'    # Yellow for WARNING
    RED = '\033[91m'       # Red for ERROR
    BOLD_RED = '\033[1;91m'  # Bold red for CRITICAL
    RESET = '\033[0m'      # Reset to default
    BOLD = '\033[1m'       # Bold text
    
    @staticmethod
    def is_terminal_supports_color():
        """Check if terminal supports ANSI colors"""
        # Windows 10+ supports ANSI in newer terminals
        if os.name == 'nt':
            # Enable ANSI support on Windows
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and better spacing"""
    
    LEVEL_COLORS = {
        logging.DEBUG: LogColors.CYAN,
        logging.INFO: LogColors.BLUE,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.BOLD_RED,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = LogColors.is_terminal_supports_color()
        self._needs_newline = False  # Track if we need to clear progress line
    
    def format(self, record):
        # Add newline only if there was a progress line before
        # This prevents multiple blank lines between consecutive log messages
        prefix = '\n' if self._needs_newline else ''
        self._needs_newline = False  # Reset after use
        
        if self.use_colors:
            # Colorize level name
            level_color = self.LEVEL_COLORS.get(record.levelno, '')
            colored_levelname = f"{level_color}{record.levelname}{LogColors.RESET}"
            record.levelname = colored_levelname
        
        formatted = super().format(record)
        return prefix + formatted

def setup_logging(level=logging.INFO):
    """Configure logging with colors and better formatting"""
    # Remove any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = ColoredFormatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Store formatter reference for progress line tracking
    root_logger._custom_formatter = formatter

# Global reference to logger's formatter for progress line tracking
def mark_progress_line_shown():
    """Mark that a progress line was shown, so next log will add newline"""
    root_logger = logging.getLogger()
    if hasattr(root_logger, '_custom_formatter'):
        root_logger._custom_formatter._needs_newline = True

# ========== TIME ADJUSTMENT FUNCTIONS ==========

def parse_time_delta(delta_str: str) -> Tuple[int, int]:
    """
    Parse a time delta string in format [+/-]YYYYMMDD_HHMMSS
    
    Args:
        delta_str: String like "+00010000_000000" (add 1 day) or "-00000000_020000" (subtract 2 hours)
    
    Returns:
        Tuple of (total_days, total_seconds)
    
    Examples:
        "+00010000_000000" -> (1, 0)  # Add 1 day
        "-00000000_020000" -> (0, -7200)  # Subtract 2 hours
        "+00000001_000000" -> (0, 2592000)  # Add 1 month (30 days approximation)
    """
    if not delta_str or len(delta_str) != 16:
        raise ValueError(f"Invalid delta format: {delta_str}. Expected format: [+/-]YYYYMMDD_HHMMSS")
    
    sign = 1 if delta_str[0] == '+' else -1
    
    # Parse date components
    year = int(delta_str[1:5])
    month = int(delta_str[5:7])
    day = int(delta_str[7:9])
    
    # Parse time components
    hour = int(delta_str[10:12])
    minute = int(delta_str[12:14])
    second = int(delta_str[14:16])
    
    # Convert everything to days and seconds
    # Note: We approximate months as 30 days and years as 365 days for simplicity
    total_days = sign * (year * 365 + month * 30 + day)
    total_seconds = sign * (hour * 3600 + minute * 60 + second)
    
    return total_days, total_seconds

def apply_time_delta(dt: datetime, delta_str: str) -> datetime:
    """
    Apply a time delta to a datetime object
    
    Args:
        dt: Original datetime
        delta_str: Delta string in format [+/-]YYYYMMDD_HHMMSS
    
    Returns:
        New datetime with delta applied
    
    Examples:
        dt = datetime(2024, 10, 15, 23, 0, 0)
        apply_time_delta(dt, "+00000000_020000")  # Add 2 hours -> 2024-10-16 01:00:00
    """
    from datetime import timedelta
    
    days, seconds = parse_time_delta(delta_str)
    delta = timedelta(days=days, seconds=seconds)
    
    return dt + delta

def load_group_time_adjustments(config_path: Path = None) -> dict:
    """
    Load time adjustments from JSON config file
    
    Args:
        config_path: Path to config file (default: specific_group_time_adjust.json in script dir)
    
    Returns:
        Dictionary mapping group names (lowercase) to delta strings
    """
    if config_path is None:
        # Default to file in same directory as script
        script_dir = Path(__file__).parent.parent
        config_path = script_dir / "specific_group_time_adjust.json"
    
    if not config_path.exists():
        logging.debug(f"No time adjustment config found at {config_path}")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            adjustments = json.load(f)
        
        # Convert keys to lowercase for case-insensitive matching
        adjustments_lower = {k.lower(): v for k, v in adjustments.items()}
        
        logging.info(f"⏰ Loaded time adjustments for {len(adjustments_lower)} group(s) from {config_path.name}")
        return adjustments_lower
    
    except Exception as e:
        logging.warning(f"⚠️  Failed to load time adjustment config: {e}")
        return {}

def adjust_datetime_for_group(dt: datetime, group_name: str, adjustments: dict) -> datetime:
    """
    Apply time adjustment to datetime if group has a configured delta
    
    Args:
        dt: Original datetime
        group_name: Name of the group (source tag)
        adjustments: Dictionary of adjustments loaded from config
    
    Returns:
        Adjusted datetime (or original if no adjustment for this group)
    """
    group_lower = group_name.lower()
    
    if group_lower in adjustments:
        delta_str = adjustments[group_lower]
        adjusted_dt = apply_time_delta(dt, delta_str)
        logging.info(f"⏰ Applied time adjustment to group '{group_name}': {delta_str}")
        logging.debug(f"   Original: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.debug(f"   Adjusted: {adjusted_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        return adjusted_dt
    
    return dt

# ========== END TIME ADJUSTMENT FUNCTIONS ==========

VIDEO_EXT_DEFAULT = ".mp4,.mov,.m4v,.avi,.mkv,.mts,.m2ts,.wmv,.3gp,.mpg,.mpeg,.insv,.360,.mod,.tod"
PHOTO_EXT_DEFAULT = ".jpg,.jpeg,.png,.tiff,.tif,.raw,.cr2,.cr3,.nef,.arw,.dng,.heic,.heif"

def is_windows():
    return os.name == "nt"

# ============================================================================
# GROUP AND FILE TYPE DETECTION (Simplified)
# ============================================================================

def get_group_from_path(file_path: Path, footage_raw_root: Path) -> str:
    """
    Get group name from immediate parent folder under footage_raw.
    
    Args:
        file_path: Path to the file
        footage_raw_root: Root footage_raw folder
        
    Returns:
        Group name (parent folder name), or "root" if directly under footage_raw
        
    Example:
        footage_raw/avata/video.mp4 → "avata"
        footage_raw/canon/IMG_001.jpg → "canon"
        footage_raw/video.mp4 → "root"
    """
    try:
        rel_path = file_path.relative_to(footage_raw_root)
        # First part of relative path is the group folder
        if rel_path.parent == Path("."):
            return "root"
        return rel_path.parts[0].lower()
    except ValueError:
        # File not under footage_raw
        return file_path.parent.name.lower() or "root"

def is_drone_group(group_name: str) -> bool:
    """
    Check if group is a drone that requires UTC conversion.
    
    Args:
        group_name: Group name from folder
        
    Returns:
        True if group is in DRONE_FOLDERS list
    """
    return group_name.lower() in DRONE_FOLDERS

def is_photo(file_path: Path) -> bool:
    """
    Check if file is a photo based on extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if extension matches photo extensions
    """
    return file_path.suffix.lower() in PHOTO_EXTENSIONS

# ============================================================================
# LEGACY COMPATIBILITY (temporary wrappers)
# ============================================================================

def _is_photo(p: Path) -> bool:
    """Legacy wrapper for is_photo()"""
    return is_photo(p)

def _path_has_drone_segment(p: Path) -> bool:
    """
    Legacy function - checks if ANY parent folder matches drone names.
    
    NOTE: This is the OLD logic. Should be replaced with:
        is_drone_group(get_group_from_path(p, footage_raw_root))
    """
    return any(part.lower() in DRONE_FOLDERS for part in p.parts)

# ============================================================================
# DATE/TIME EXTRACTION FUNCTIONS
# ============================================================================

def _ffprobe_creation_time(path: Path) -> tuple[Optional[str], Optional[str]]:
    """
    Retourne (iso_str, source_tag) ou (None, None)
    """
    try:
        cmd = ["ffprobe","-v","error","-print_format","json","-show_entries",
               "format_tags=creation_time:stream_tags=creation_time", str(path)]
        out = subprocess.check_output(cmd, text=True)
        j = json.loads(out)

        fmt = (j.get("format", {}) or {}).get("tags", {}) or {}
        if "creation_time" in fmt:
            return fmt["creation_time"], "format.tags.creation_time"

        streams = j.get("streams", []) or []
        if streams and "tags" in streams[0] and "creation_time" in (streams[0]["tags"] or {}):
            return streams[0]["tags"]["creation_time"], "streams[0].tags.creation_time"

        return None, None
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        logging.debug(f"ffprobe creation_time failed for {path}: {e}")
        return None, None

def _exiftool_quicktime_datetime(path: Path) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Utilise exiftool pour extraire QuickTime:DateTimeOriginal pour les fichiers iPhone/Apple
    Retourne (iso_str, source_tag, exiftool_output) ou (None, None, error_message)
    """
    try:
        # Utiliser exiftool pour extraire spécifiquement QuickTime:DateTimeOriginal
        cmd = ["exiftool", "-QuickTime:DateTimeOriginal", "-d", "%Y-%m-%dT%H:%M:%S", "-s3", str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            datetime_str = result.stdout.strip()
            if datetime_str != "-":  # exiftool returns "-" when no data
                # Convert to ISO format (assuming local time)
                iso_str = datetime_str + "+00:00"  # Add timezone indicator
                return iso_str, "exiftool.QuickTime:DateTimeOriginal", f"✅ exiftool success: {datetime_str}"
            else:
                # Try fallback to regular DateTimeOriginal if QuickTime version not found
                cmd_fallback = ["exiftool", "-DateTimeOriginal", "-d", "%Y-%m-%dT%H:%M:%S", "-s3", str(path)]
                result_fallback = subprocess.run(cmd_fallback, capture_output=True, text=True, timeout=10)
                
                if result_fallback.returncode == 0 and result_fallback.stdout.strip() and result_fallback.stdout.strip() != "-":
                    datetime_str = result_fallback.stdout.strip()
                    iso_str = datetime_str + "+00:00"
                    return iso_str, "exiftool.DateTimeOriginal", f"✅ exiftool success (fallback): {datetime_str}"
                else:
                    return None, None, "❌ exiftool: No QuickTime:DateTimeOriginal or DateTimeOriginal found"
        else:
            error_msg = result.stderr.strip() if result.stderr.strip() else "Unknown error"
            return None, None, f"❌ exiftool failed: {error_msg}"
            
    except FileNotFoundError:
        return None, None, "❌ exiftool not found - install from https://exiftool.org/"
    except subprocess.TimeoutExpired:
        return None, None, "❌ exiftool timed out (>10 seconds)"
    except Exception as e:
        return None, None, f"❌ exiftool exception: {str(e)}"

def _get_exiftool_datetime_unified(path: Path) -> tuple[Optional[str], str]:
    """
    Fonction unifiée qui exécute exactement la même commande exiftool que dans copy_file()
    Retourne (datetime_string, status_message)
    """
    try:
        # Commande principale : QuickTime:DateTimeOriginal
        cmd = ["exiftool", "-QuickTime:DateTimeOriginal", "-d", "%Y-%m-%dT%H:%M:%S", "-s3", str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output and output != "-":
                return output, f"✅ SUCCESS: {output}"
            else:
                # Fallback 1: regular DateTimeOriginal
                cmd_fallback1 = ["exiftool", "-DateTimeOriginal", "-d", "%Y-%m-%dT%H:%M:%S", "-s3", str(path)]
                result_fallback1 = subprocess.run(cmd_fallback1, capture_output=True, text=True, timeout=10)
                
                if result_fallback1.returncode == 0:
                    output_fallback1 = result_fallback1.stdout.strip()
                    if output_fallback1 and output_fallback1 != "-":
                        return output_fallback1, f"✅ SUCCESS (DateTimeOriginal fallback): {output_fallback1}"
                
                # Fallback 2: QuickTime:CreationDate
                cmd_fallback2 = ["exiftool", "-QuickTime:CreationDate", "-d", "%Y-%m-%dT%H:%M:%S", "-s3", str(path)]
                result_fallback2 = subprocess.run(cmd_fallback2, capture_output=True, text=True, timeout=10)
                
                if result_fallback2.returncode == 0:
                    output_fallback2 = result_fallback2.stdout.strip()
                    if output_fallback2 and output_fallback2 != "-":
                        return output_fallback2, f"✅ SUCCESS (QuickTime:CreationDate fallback): {output_fallback2}"
                
                return None, "⚠️ No QuickTime:DateTimeOriginal, DateTimeOriginal, or QuickTime:CreationDate found"
        else:
            error_msg = result.stderr.strip() if result.stderr.strip() else "Unknown error"
            return None, f"❌ FAILED: {error_msg}"
            
    except FileNotFoundError:
        return None, "❌ exiftool not found - install from https://exiftool.org/"
    except subprocess.TimeoutExpired:
        return None, "❌ exiftool timed out"
    except Exception as e:
        return None, f"❌ exiftool exception: {str(e)}"

def _extract_datetime_with_fallback(path: Path, tz_name: str = "America/Montreal") -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Fonction universelle d'extraction de datetime avec fallback intelligent
    1. Essaie ffprobe d'abord
    2. Si pas de résultat et pas de date dans le nom de fichier, essaie exiftool QuickTime
    Retourne (iso_str, source_tag, exiftool_info)
    """
    # Essayer ffprobe d'abord
    iso, src = _ffprobe_creation_time(path)
    exiftool_info = None
    
    if not iso:
        # Si pas de métadonnées ffprobe et pas de date dans le nom de fichier,
        # essayer exiftool pour les données QuickTime (iPhone/Apple)
        has_filename_date = _has_filename_datetime(path)
        if not has_filename_date:
            logging.debug(f"No ffprobe data and no filename date, trying exiftool: {path}")
            iso, src, exiftool_info = _exiftool_quicktime_datetime(path)
            if iso:
                logging.info(f"Found datetime via exiftool QuickTime: {iso} from {src}")
        else:
            exiftool_info = "⚠️ Skipped exiftool (filename has date)"
    else:
        exiftool_info = "⚠️ Skipped exiftool (ffprobe found data)"
    
    return iso, src, exiftool_info

def _has_filename_datetime(path: Path) -> bool:
    """
    Vérifie si le nom du fichier contient une date/heure
    Détecte les formats: YYYYMMDD, YYYY-MM-DD, YYYYMMDD_HHMMSS, etc.
    """
    filename = path.name
    import re
    
    # Patterns pour détecter les dates dans le nom de fichier
    patterns = [
        r'\d{8}',           # YYYYMMDD
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{8}_\d{6}',     # YYYYMMDD_HHMMSS
        r'\d{14}',          # YYYYMMDDHHMMSS
    ]
    
    for pattern in patterns:
        if re.search(pattern, filename):
            return True
    
    return False

def _path_has_cell_segment(p: Path) -> bool:
    """Vérifie si le chemin contient un dossier commençant par 'cell'"""
    return any(part.lower().startswith("cell") for part in p.parts)

def detect_video_source_type(path: Path, footage_raw_path: Path) -> dict:
    """
    Détecte le type de source vidéo basé sur le chemin de manière modulaire
    Utilise le premier sous-dossier sous footage_raw comme source tag
    
    Args:
        path: Chemin du fichier vidéo
        footage_raw_path: Chemin du dossier footage_raw pour calculer le relatif
    
    Retourne un dictionnaire avec le type de source et des tags associés
    """
    source_info = {
        "source_type": "Unknown",
        "source_tag": "UNKNOWN",
        "device_category": "Generic"
    }
    
    try:
        # Calculer le chemin relatif depuis footage_raw
        relative_path = path.relative_to(footage_raw_path)
        parts = relative_path.parts
        
        # Le premier élément du chemin relatif est le dossier source
        if len(parts) > 1:  # Il faut au moins un dossier + le fichier
            subfolder_name = parts[0]  # Premier sous-dossier sous footage_raw
        else:
            # Fichier directement dans footage_raw (cas rare)
            subfolder_name = "ROOT"
        
        
        # Nettoyer le nom et créer le source tag
        clean_name = subfolder_name.replace("_", "-").upper()
        source_info["source_tag"] = clean_name
        source_info["source_type"] = subfolder_name
        
        # Détection de catégorie basée sur des mots-clés simples
        subfolder_lower = subfolder_name.lower()
        
        if subfolder_lower.startswith("drone") or subfolder_lower.startswith("dji") or "videos" in subfolder_lower:
            source_info["device_category"] = "Aerial"
        elif subfolder_lower.startswith("cell"):
            source_info["device_category"] = "Mobile"
        elif "gopro" in subfolder_lower:
            source_info["device_category"] = "Action Camera"
        elif "camera" in subfolder_lower or "cam" in subfolder_lower:
            source_info["device_category"] = "Photo/Video Camera"
        else:
            source_info["device_category"] = "Other"
    
    except Exception as e:
        logging.debug(f"Erreur détection source pour {path}: {e}")
    
    return source_info

def extract_video_metadata(path: Path) -> dict:
    """
    Extrait les métadonnées techniques d'une vidéo avec ffprobe
    Retourne un dictionnaire avec résolution, framerate, codec, colorspace, etc.
    """
    try:
        cmd = ["ffprobe", "-v", "error", "-print_format", "json", 
               "-show_entries", "stream=codec_type,width,height,r_frame_rate,avg_frame_rate,codec_name,pix_fmt,color_space,color_transfer,color_primaries:format=duration,bit_rate,format_name", 
               str(path)]
        out = subprocess.check_output(cmd, text=True, timeout=10)
        j = json.loads(out)
        
        metadata = {}
        
        # Informations du format
        format_info = j.get("format", {})
        if format_info:
            metadata["duration"] = format_info.get("duration")
            metadata["bit_rate"] = format_info.get("bit_rate")
            metadata["format_name"] = format_info.get("format_name")
        
        # Informations du premier stream vidéo
        streams = j.get("streams", [])
        video_stream = None
        
        # Chercher le premier stream vidéo
        for stream in streams:
            # Vérifier si c'est un stream vidéo (codec_type ou présence de width/height)
            if (stream.get("codec_type") == "video" or 
                (stream.get("width") and stream.get("height"))):
                video_stream = stream
                break
        
        if video_stream:
            # Résolution
            width = video_stream.get("width")
            height = video_stream.get("height")
            if width and height:
                metadata["resolution"] = f"{width}x{height}"
            
            # Frame rate
            r_frame_rate = video_stream.get("r_frame_rate")
            if r_frame_rate and "/" in str(r_frame_rate):
                try:
                    num, den = map(int, r_frame_rate.split("/"))
                    if den != 0:
                        fps = num / den
                        metadata["frame_rate"] = f"{fps:.2f} fps"
                except:
                    metadata["frame_rate"] = str(r_frame_rate)
            
            # Codec
            metadata["codec"] = video_stream.get("codec_name")
            
            # Format de pixel
            metadata["pixel_format"] = video_stream.get("pix_fmt")
            
            # Informations couleur
            color_space = video_stream.get("color_space")
            color_transfer = video_stream.get("color_transfer")
            color_primaries = video_stream.get("color_primaries")
            pix_fmt = video_stream.get("pix_fmt")
            
            if color_space:
                metadata["color_space"] = color_space
            if color_transfer:
                metadata["color_transfer"] = color_transfer
            if color_primaries:
                metadata["color_primaries"] = color_primaries
                
            # Détection avancée HDR/Log basée sur plusieurs critères
            is_hdr_log = False
            hdr_indicators = []
            
            # 1. Color transfer patterns
            if color_transfer:
                transfer_lower = str(color_transfer).lower()
                if any(indicator in transfer_lower for indicator in ["log", "pq", "smpte2084", "hlg", "arib-std-b67"]):
                    is_hdr_log = True
                    hdr_indicators.append(f"transfer: {color_transfer}")
            
            # 2. Color space patterns (BT.2020 often indicates HDR)
            if color_space:
                space_lower = str(color_space).lower()
                if "bt2020" in space_lower or "rec2020" in space_lower:
                    is_hdr_log = True
                    hdr_indicators.append(f"colorspace: {color_space}")
            
            # 3. Color primaries patterns
            if color_primaries:
                primaries_lower = str(color_primaries).lower()
                if "bt2020" in primaries_lower or "rec2020" in primaries_lower:
                    is_hdr_log = True
                    hdr_indicators.append(f"primaries: {color_primaries}")
            
            # 4. Pixel format patterns (10-bit+ often indicates HDR/Log)
            if pix_fmt:
                fmt_lower = str(pix_fmt).lower()
                if any(indicator in fmt_lower for indicator in ["10le", "12le", "16le", "p010", "p016"]):
                    is_hdr_log = True
                    hdr_indicators.append(f"10+ bit: {pix_fmt}")
            
            # Set the is_log metadata
            if is_hdr_log:
                metadata["is_log"] = f"YES - HDR/Log detected ({', '.join(hdr_indicators)})"
                metadata["hdr_tag"] = "HDR/LOG"  # Tag facile à repérer
            else:
                metadata["is_log"] = "No (Standard SDR)"
                metadata["hdr_tag"] = "SDR"
        
        return metadata
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        logging.debug(f"ffprobe metadata extraction failed for {path}: {e}")
        return {}

def get_raw_ffprobe_metadata(path: Path) -> dict:
    """
    Obtient toutes les données brutes de ffprobe en format JSON
    Pour inclusion dans les placeholders JSON
    """
    try:
        cmd = ["ffprobe", "-v", "error", "-print_format", "json", 
               "-show_format", "-show_streams", str(path)]
        out = subprocess.check_output(cmd, text=True, timeout=30)
        return json.loads(out)
    except Exception as e:
        logging.debug(f"Raw ffprobe extraction failed for {path}: {e}")
        return {"error": str(e)}

def get_raw_exiftool_metadata(path: Path) -> dict:
    """
    Obtient toutes les données brutes d'exiftool en format JSON
    Pour inclusion dans les placeholders JSON
    """
    try:
        cmd = ["exiftool", "-j", "-G", "-a", str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return data[0] if data and len(data) > 0 else {}
        return {"error": result.stderr if result.stderr else "No output from exiftool"}
    except FileNotFoundError:
        return {"error": "exiftool not installed"}
    except Exception as e:
        logging.debug(f"Raw exiftool extraction failed for {path}: {e}")
        return {"error": str(e)}

def extract_times_for_drone_file(path: Path, tz_name: str = "America/Montreal"):
    if not _path_has_drone_segment(path):
        logging.info(f"Skipping (not under 'drone'): {path}")
        return None

    # Check if this is a stabilized file
    if path.stem.endswith("_stabilized"):
        # For stabilized files, try to find the original file and use its metadata
        original_path = path.parent / (path.stem[:-11] + path.suffix)  # Remove "_stabilized"
        if original_path.exists():
            logging.info(f"Using original file metadata for stabilized file: {original_path.name} -> {path.name}")
            return extract_times_for_drone_file(original_path, tz_name)
        else:
            logging.warning(f"Stabilized file found but original missing: {path}")
            # Continue with normal processing for stabilized file

    iso, src, exiftool_info = _extract_datetime_with_fallback(path, tz_name)
    
    if not iso:
        logging.warning(f"No creation_time in metadata (tried ffprobe and exiftool): {path}")
        # Store exiftool info for later use in placeholder file
        if hasattr(path, '_exiftool_debug_info'):
            path._exiftool_debug_info = exiftool_info
        return None

    try:
        # Get file mtime for comparison
        mtime_timestamp = path.stat().st_mtime
        mtime_dt = datetime.fromtimestamp(mtime_timestamp)
        
        # Parse the metadata time as if it were local time (no timezone conversion)
        iso_norm = iso.replace("Z", "+00:00")
        dt_metadata_raw = datetime.fromisoformat(iso_norm).replace(tzinfo=None)
        
        # Compare raw metadata time directly with mtime (both in local time)
        # Allow 5 minutes tolerance
        time_diff = abs((dt_metadata_raw - mtime_dt).total_seconds())
        tolerance_seconds = 5 * 60  # 5 minutes
        
        if time_diff <= tolerance_seconds:
            # Times are close - metadata is probably already in local time, use mtime
            logging.info(f"Raw metadata time ({dt_metadata_raw.strftime('%Y-%m-%d %H:%M:%S')}) is close to mtime ({mtime_dt.strftime('%Y-%m-%d %H:%M:%S')}), using mtime")
            dt_final = mtime_dt
            time_source = "mtime (metadata appears to be local time)"
        else:
            # Times are different - metadata is probably real UTC, need conversion
            tz = zoneinfo.ZoneInfo(tz_name)
            # Parse as UTC explicitly (iso_norm has +00:00 or Z)
            dt_metadata_utc = datetime.fromisoformat(iso_norm).replace(tzinfo=timezone.utc)
            # Convert to target timezone
            dt_metadata_local = dt_metadata_utc.astimezone(tz)
            
            logging.info(f"Raw metadata time ({dt_metadata_raw.strftime('%Y-%m-%d %H:%M:%S')}) differs from mtime ({mtime_dt.strftime('%Y-%m-%d %H:%M:%S')}) by {time_diff/60:.1f} minutes, using converted UTC")
            dt_final = dt_metadata_local.replace(tzinfo=None)
            time_source = f"converted UTC from {src}"

        # Create return data based on chosen time
        # Always create UTC reference for consistency
        if time_diff <= tolerance_seconds:
            # If we used mtime, create a fake UTC for consistency
            utc_iso = mtime_dt.isoformat() + "Z"
        else:
            # dt_metadata_utc already created above with proper UTC timezone
            utc_iso = dt_metadata_utc.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        
        local_iso = dt_final.isoformat()

        return {
            "utc_iso": utc_iso,
            "local_iso": local_iso,
            "local_date": dt_final.strftime("%Y-%m-%d"),
            "local_time": dt_final.strftime("%H-%M-%S"),
            "source_tag": time_source,
            "time_diff_minutes": time_diff / 60
        }
    except (ValueError, KeyError, zoneinfo.ZoneInfoNotFoundError) as e:
        logging.warning(f"Failed to parse datetime {iso} for {path}: {e}")
        return None

def list_timezones():
    try:
        tzs = sorted(zoneinfo.available_timezones())
        if not tzs:
            print("Aucune timezone listée. Installe le package 'tzdata' sur ce système.")
        else:
            for t in tzs:
                print(t)
    except Exception as e:
        print(f"Impossible de lister les timezones ({e}). Suggéré: installer 'tzdata'.")

def parse_args():
    p = argparse.ArgumentParser(description="Create a date-/source-sorted view of your footage using text placeholders (no file moves).")
    p.add_argument("input_dir", nargs='?', type=Path, help="Project root folder containing Footage_raw/ subdirectory")
    p.add_argument("output_dir", nargs='?', type=Path, help="Where to create the organized placeholders (default: Footage_metadata_sorted in project root)")
    p.add_argument("--ext", default=VIDEO_EXT_DEFAULT,
                   help=f"Comma-separated list of video file extensions (case-insensitive). Default: {VIDEO_EXT_DEFAULT}")
    p.add_argument("--photo-ext", default=PHOTO_EXT_DEFAULT,
                   help=f"Comma-separated list of photo file extensions (case-insensitive). Default: {PHOTO_EXT_DEFAULT}")
    p.add_argument("--photos-only", action="store_true",
                   help="Process only photos (skip videos)")
    p.add_argument("--videos-only", action="store_true", 
                   help="Process only videos (skip photos)")
    p.add_argument("--include-photos", action="store_true",
                   help="Process both videos and photos (photos go in separate 'photos' subfolder)")
    p.add_argument("--use-mtime", action="store_true",
                   help="Use file's *modified* time (default). (Kept for symmetry; default is mtime)")
    p.add_argument("--simulate", action="store_true",
                   help="Dry-run. Print what would be created without writing anything.")
    p.add_argument("--tz", default="America/Montreal",
                   help="Timezone for drone file metadata conversion (default: America/Montreal)")
    p.add_argument("--list-tz", action="store_true",
                   help="List available timezones and exit")
    return p.parse_args()

def list_media_files(root: Path, video_extensions="", photo_extensions="", videos_only=False, photos_only=False):
    """List media files (videos and/or photos) with their type, prioritizing _stabilized versions and filtering out originals when stabilized exists"""
    video_exts = {e.strip().lower() for e in video_extensions.split(",") if e.strip()} if video_extensions else set()
    photo_exts = {e.strip().lower() for e in photo_extensions.split(",") if e.strip()} if photo_extensions else set()
    
    # First pass: collect all files grouped by base name
    file_groups = {}  # (parent_dir, base_name, extension) -> {"original": path, "stabilized": path}
    
    for p in root.rglob("*"):
        if p.is_file():
            ext = p.suffix.lower()
            file_type = None
            
            if not photos_only and ext in video_exts:
                file_type = "video"
            elif not videos_only and ext in photo_exts:
                file_type = "photo"
            
            if file_type:
                # Determine base name (remove _stabilized suffix if present)
                stem = p.stem
                # Handle various stabilized suffixes (case insensitive)
                stem_lower = stem.lower()
                if stem_lower.endswith("_stabilized"):
                    base_name = stem[:-11]  # Remove "_stabilized"
                    is_stabilized = True
                elif stem_lower.endswith(" stabilized"):  # Handle space instead of underscore
                    base_name = stem[:-11]  # Remove " stabilized"
                    is_stabilized = True
                else:
                    base_name = stem
                    is_stabilized = False
                
                # Normalize base name (remove trailing/leading spaces)
                base_name = base_name.strip()
                
                # Use lowercase extension for consistent grouping
                group_key = (p.parent, base_name, ext)  # ext is already lowercase
                
                if group_key not in file_groups:
                    file_groups[group_key] = {}
                
                if is_stabilized:
                    file_groups[group_key]["stabilized"] = (p, file_type)
                else:
                    file_groups[group_key]["original"] = (p, file_type)
    
    # Second pass: yield only the best version for each group
    skipped_count = 0
    for group_key, versions in file_groups.items():
        if "stabilized" in versions:
            # Stabilized version exists - use it and skip original
            path, file_type = versions["stabilized"]
            yield path, file_type
            if "original" in versions:
                skipped_count += 1
                logging.debug(f"⏭️  Skipped original (stabilized exists): {versions['original'][0].name}")
        elif "original" in versions:
            # Only original version exists - use it
            path, file_type = versions["original"]
            yield path, file_type
    
    if skipped_count > 0:
        print(f"📋 Filtered out {skipped_count} original files (stabilized versions exist)")
        logging.info(f"✅ Total original files skipped: {skipped_count} (using stabilized versions)")

def list_videos(root: Path, extensions):
    """Legacy function for backward compatibility - only videos"""
    for file_path, file_type in list_media_files(root, extensions, "", videos_only=True):
        yield file_path

def extract_time_from_file(file_path: Path, tz_name: str = "America/Montreal", group_name: str = None, time_adjustments: dict = None):
    """Extract time from filename first, then fallback to drone metadata, then file metadata
    
    Args:
        file_path: Path to the file
        tz_name: Timezone name for drone files
        group_name: Source group name for time adjustments
        time_adjustments: Dictionary of time adjustments per group
    
    Returns:
        Time string in format "HHhMMmSSs" or special markers
    """
    filename = file_path.name
    import re
    
    # Check if this is a stabilized file and try to use original file's time
    if file_path.stem.endswith("_stabilized"):
        # For stabilized files, try to find the original file and use its time
        original_path = file_path.parent / (file_path.stem[:-11] + file_path.suffix)  # Remove "_stabilized"
        if original_path.exists():
            logging.info(f"Using original file time for stabilized file: {original_path.name} -> {file_path.name}")
            return extract_time_from_file(original_path, tz_name, group_name, time_adjustments)
        else:
            logging.warning(f"Stabilized file found but original missing: {file_path}")
            # Continue with normal processing for stabilized file
    
    # Helper function to apply time adjustment to datetime
    def apply_adjustment(dt: datetime) -> datetime:
        """Apply time adjustment if configured"""
        if time_adjustments and group_name:
            return adjust_datetime_for_group(dt, group_name, time_adjustments)
        return dt
    
    # For drone files, try QuickTime metadata extraction FIRST (priority over filename)
    if _path_has_drone_segment(file_path):
        drone_data = extract_times_for_drone_file(file_path, tz_name)
        if drone_data:
            # Parse the local datetime and apply adjustment
            local_date_str = drone_data["local_date"]
            local_time_str = drone_data["local_time"]
            try:
                dt_str = f"{local_date_str} {local_time_str.replace('-', ':')}"
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                # Apply adjustment
                dt_adjusted = apply_adjustment(dt)
                return f"{dt_adjusted.hour:02d}h{dt_adjusted.minute:02d}m{dt_adjusted.second:02d}s"
            except ValueError:
                pass
    
    # For non-drone files, try to extract time from filename first
    # Format: 20250821_051728 or 20250821051728 (last 6 digits are HHMMSS)
    
    # Pattern 1: YYYYMMDD_HHMMSS
    pattern1 = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', filename)
    if pattern1:
        year, month, day, h, m, s = pattern1.groups()
        # Validate values
        try:
            dt = datetime(int(year), int(month), int(day), int(h), int(m), int(s))
            if 1990 <= dt.year <= 2030 and 0 <= dt.hour <= 23:
                # Apply adjustment
                dt_adjusted = apply_adjustment(dt)
                return f"{dt_adjusted.hour:02d}h{dt_adjusted.minute:02d}m{dt_adjusted.second:02d}s"
        except ValueError:
            pass
    
    # Pattern 2: YYYYMMDDHHMMSS (14 digits total)
    pattern2 = re.search(r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', filename)
    if pattern2:
        year, month, day, h, m, s = pattern2.groups()
        # Validate values
        try:
            dt = datetime(int(year), int(month), int(day), int(h), int(m), int(s))
            if 1990 <= dt.year <= 2030 and 0 <= dt.hour <= 23:
                # Apply adjustment
                dt_adjusted = apply_adjustment(dt)
                return f"{dt_adjusted.hour:02d}h{dt_adjusted.minute:02d}m{dt_adjusted.second:02d}s"
        except ValueError:
            pass
    
    # For non-drone files without filename time, try exiftool (iPhone/Apple) - UNIFIED VERSION
    has_filename_date = _has_filename_datetime(file_path)
    if not has_filename_date:
        datetime_str, status = _get_exiftool_datetime_unified(file_path)
        
        if datetime_str:
            try:
                dt = datetime.fromisoformat(datetime_str + "+00:00").replace(tzinfo=None)
                # Apply adjustment
                dt_adjusted = apply_adjustment(dt)
                logging.debug(f"📅 Extracted time from exiftool for {file_path.name}: {dt_adjusted.strftime('%H:%M:%S')}")
                return f"{dt_adjusted.hour:02d}h{dt_adjusted.minute:02d}m{dt_adjusted.second:02d}s"
            except ValueError as e:
                logging.warning(f"Failed to parse exiftool time {datetime_str}: {e}")
                # Will return "KEEP_ORIGINAL" to trigger special handling
        
        # If exiftool failed, mark for fallback to mtime (will be handled in main loop)
        logging.debug(f"No metadata found for {file_path.name} - will use mtime as fallback")
        return "KEEP_ORIGINAL"
    
    # Fallback to file metadata
    try:
        ts = file_path.stat().st_mtime
        dt = datetime.fromtimestamp(ts)
        # Check if metadata date is reasonable
        if 1990 <= dt.year <= 2300:
            # Apply adjustment
            dt_adjusted = apply_adjustment(dt)
            return f"{dt_adjusted.hour:02d}h{dt_adjusted.minute:02d}m{dt_adjusted.second:02d}s"
    except Exception:
        pass
    
    # If nothing works, return special marker to keep original name
    return "KEEP_ORIGINAL"

def remove_temporal_elements(filename: str, file_type: str = "video"):
    """Remove date and time elements from filename, preserving _stabilized suffix"""
    import re
    
    # Check if filename has _stabilized suffix and preserve it
    has_stabilized = filename.endswith('_stabilized.mp4') or filename.endswith('_stabilized.MP4')
    if has_stabilized:
        # Remove the _stabilized suffix temporarily
        if filename.lower().endswith('_stabilized.mp4'):
            base_filename = filename[:-15] + filename[-4:]  # Remove "_stabilized" but keep ".mp4"
        else:
            base_filename = filename
        stabilized_suffix = "_stabilized"
    else:
        base_filename = filename
        stabilized_suffix = ""
    
    # Remove YYYYMMDD patterns
    clean_filename = re.sub(r'\d{8}', '', base_filename)
    
    # Remove YYYY-MM-DD patterns
    clean_filename = re.sub(r'\d{4}-\d{2}-\d{2}', '', clean_filename)
    
    # Remove time patterns (HHMMSS, HH:MM:SS, HH-MM-SS, HH_MM_SS)
    clean_filename = re.sub(r'\d{6}', '', clean_filename)
    clean_filename = re.sub(r'\d{2}[:_-]\d{2}[:_-]\d{2}', '', clean_filename)
    
    # Remove leading/trailing underscores and clean up
    clean_filename = re.sub(r'^[_-]+|[_-]+$', '', clean_filename)
    clean_filename = re.sub(r'[_-]+', '_', clean_filename)
    
    # If filename becomes empty or just extension, use a placeholder based on file type
    if '.' in clean_filename:
        name_part = clean_filename.split('.')[0]
        ext = '.' + clean_filename.split('.')[-1]
    else:
        name_part = clean_filename
        ext = ''
    
    if not name_part or name_part.strip('_-') == '':
        base_name = "photo" if file_type == "photo" else "video"
        clean_filename = base_name + ext
    
    # Add back the _stabilized suffix before the extension if it was present
    if has_stabilized and '.' in clean_filename:
        name_part = clean_filename.rsplit('.', 1)[0]
        ext = '.' + clean_filename.rsplit('.', 1)[1]
        clean_filename = name_part + stabilized_suffix + ext
    elif has_stabilized:
        clean_filename = clean_filename + stabilized_suffix
    
    return clean_filename

def file_date(p: Path, tz_name: str = "America/Montreal", group_name: str = None, time_adjustments: dict = None):
    """
    Extract date from file with optional time adjustment per group
    
    Args:
        p: Path to file
        tz_name: Timezone name for conversion
        group_name: Source group name (for time adjustments)
        time_adjustments: Dictionary of time adjustments per group
    
    Returns:
        datetime.date object or None if invalid
        
    Note: Time adjustments are applied to dates extracted from metadata.
    For files without time information, adjustments use midnight as the time.
    """
    # Check if this is a stabilized file and try to use original file's date
    if p.stem.endswith("_stabilized"):
        # For stabilized files, try to find the original file and use its date
        original_path = p.parent / (p.stem[:-11] + p.suffix)  # Remove "_stabilized"
        if original_path.exists():
            logging.debug(f"🔄 Using original file date for stabilized: {original_path.name}")
            return file_date(original_path, tz_name, group_name, time_adjustments)
        else:
            logging.warning(f"⚠️  Stabilized file found but original missing: {p}")
            # Continue with normal processing for stabilized file
    
    # Helper function to apply adjustments before returning
    def apply_adjustment_and_return(dt_obj):
        """Apply time adjustment if configured and return date"""
        if time_adjustments and group_name:
            adjusted_dt = adjust_datetime_for_group(dt_obj, group_name, time_adjustments)
            return adjusted_dt.date()
        return dt_obj.date() if isinstance(dt_obj, datetime) else dt_obj
    
    # For drone files, handle differently for videos vs photos
    if _path_has_drone_segment(p):
        # For drone VIDEOS: try QuickTime metadata first (more reliable than filename)
        if not _is_photo(p):
            drone_data = extract_times_for_drone_file(p, tz_name)
            if drone_data:
                # Use the local datetime from QuickTime metadata
                local_date_str = drone_data["local_date"]
                local_time_str = drone_data["local_time"]
                try:
                    # Combine date and time to get full datetime
                    dt_str = f"{local_date_str} {local_time_str.replace('-', ':')}"
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    return apply_adjustment_and_return(dt)
                except ValueError:
                    pass
        # For drone PHOTOS: use mtime with adjustment
        else:
            ts = p.stat().st_mtime
            # mtime is in local system time, but we want to interpret it in the specified timezone
            # First, get the datetime as if it's in the target timezone
            dt_naive = datetime.fromtimestamp(ts)
            
            # If tz_name is different from system timezone, we need to adjust
            # However, mtime is already in system local time, so we just use it as-is
            # The timezone parameter is mainly for drone VIDEO metadata conversion (UTC -> local)
            dt = dt_naive
            logging.debug(f"📸 Using mtime for drone photo {p.name}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            # Apply adjustment if configured
            return apply_adjustment_and_return(dt)
    
    # For non-drone files (iPhone/Apple), try exiftool if no filename date - UNIFIED VERSION
    else:
        has_filename_date = _has_filename_datetime(p)
        if not has_filename_date:
            # Try unified exiftool for iPhone/Apple files
            datetime_str, status = _get_exiftool_datetime_unified(p)
            
            if datetime_str:
                try:
                    # Parse the datetime and extract date
                    dt = datetime.fromisoformat(datetime_str + "+00:00").replace(tzinfo=None)
                    logging.info(f"📅 Using metadata date for {p.name}: {dt.date()}")
                    return apply_adjustment_and_return(dt)
                except ValueError as e:
                    logging.warning(f"Failed to parse exiftool datetime {datetime_str}: {e}")
                    # Will fall through to filename/mtime extraction
            else:
                # exiftool failed, will be placed in date_non_valide later
                logging.debug(f"exiftool returned no date for {p.name}")
                # Don't return None here yet, let it try filename patterns first
    
    # Try to extract date from filename first (more reliable for camera files)
    filename = p.name
    
    # Common patterns: YYYYMMDD_HHMMSS, YYYY-MM-DD, etc.
    import re
    
    # Pattern for YYYYMMDD format in filename
    pattern1 = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
    if pattern1:
        try:
            year, month, day = pattern1.groups()
            dt = datetime(int(year), int(month), int(day))
            # Sanity check: reasonable date range
            if 1990 <= dt.year <= 2030:
                return apply_adjustment_and_return(dt)
        except ValueError:
            pass
    
    # Pattern for YYYY-MM-DD format in filename  
    pattern2 = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if pattern2:
        try:
            year, month, day = pattern2.groups()
            dt = datetime(int(year), int(month), int(day))
            if 1990 <= dt.year <= 2030:
                return apply_adjustment_and_return(dt)
        except ValueError:
            pass
    
    # Fallback to file system date, but with sanity check
    ts = p.stat().st_mtime
    dt = datetime.fromtimestamp(ts)
    
    # If file date is unreasonable, return None to indicate invalid date
    if dt.year < 1990 or dt.year > 2030:
        print(f"[WARN] File {filename} has invalid date {dt.date()}, will be placed in 'date_non_valide' folder")
        return None
    
    return apply_adjustment_and_return(dt)

def source_name(p: Path, input_root: Path):
    # Take immediate parent segment under input_root as "source"
    try:
        rel = p.relative_to(input_root)
        # source is first part of rel.parent, or "root" if file is directly under input_root
        if rel.parent == Path("."):
            return "root"
        return rel.parts[0]
    except ValueError:
        # Not under input_root; fallback to parent name
        return p.parent.name or "root"

def ensure_dir(d: Path, simulate=False):
    if simulate:
        return
    d.mkdir(parents=True, exist_ok=True)

def unique_path(basepath: Path) -> Path:
    # If a file exists, append _001, _002, ...
    if not basepath.exists():
        return basepath
    stem = basepath.stem
    suffix = basepath.suffix
    parent = basepath.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i:03d}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1

def create_symlink(target: Path, link_path: Path, simulate=False):
    if simulate:
        return True
    try:
        # Remove if exists (should not usually due to unique_path, but safe)
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        os.symlink(target, link_path)
        return True
    except OSError as e:
        print(f"[WARN] Symlink failed: {e}")
        return False

def create_hardlink(target: Path, link_path: Path, simulate=False):
    if simulate:
        return True
    try:
        # Check if target and destination are on same drive (required for hardlinks)
        target_drive = str(target).split(':')[0].upper() if ':' in str(target) else None
        link_drive = str(link_path).split(':')[0].upper() if ':' in str(link_path) else None
        
        if target_drive and link_drive and target_drive != link_drive:
            print(f"[WARN] Cannot create hardlink across drives ({target_drive}: -> {link_drive}:)")
            return False
            
        if link_path.exists():
            link_path.unlink()
        os.link(target, link_path)
        return True
    except OSError as e:
        # Common errors:
        # WinError 1: Incorrect function (filesystem doesn't support hardlinks)
        # WinError 17: The system cannot move the file to a different disk drive
        if e.winerror == 1:
            print(f"[WARN] Hardlink not supported by filesystem")
        elif e.winerror == 17:
            print(f"[WARN] Cannot create hardlink across different drives")
        else:
            print(f"[WARN] Hardlink failed: {e}")
        return False

def create_windows_lnk(target: Path, link_path: Path, simulate=False):
    """
    Create a .lnk file via PowerShell. No external Python deps.
    Note: .lnk is Windows-only and not portable to macOS/Linux.
    """
    if simulate:
        return True
    try:
        # Ensure .lnk extension
        if link_path.suffix.lower() != ".lnk":
            link_path = link_path.with_suffix(link_path.suffix + ".lnk")
        
        # Remove existing file if it exists
        if link_path.exists():
            link_path.unlink()
            
        # PowerShell script to create shortcut with better error handling
        target_str = str(target).replace("'", "''")  # Escape single quotes
        link_str = str(link_path).replace("'", "''")  # Escape single quotes
        
        ps = f"""
        try {{
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut('{link_str}')
            $Shortcut.TargetPath = '{target_str}'
            $Shortcut.WindowStyle = 1
            $Shortcut.Save()
            Write-Host 'Success'
        }} catch {{
            Write-Error $_.Exception.Message
            exit 1
        }}
        """
        
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], 
            capture_output=True, text=True, timeout=10
        )
        
        if completed.returncode != 0:
            print(f"[WARN] PowerShell .lnk creation failed: {completed.stderr.strip()}")
            return False
        return True
        
    except subprocess.TimeoutExpired:
        print("[WARN] PowerShell .lnk creation timed out")
        return False
    except Exception as e:
        print(f"[WARN] .lnk creation exception: {e}")
        return False

def _get_exiftool_debug_info(path: Path) -> str:
    """
    Obtient les informations de debug exiftool pour inclure dans le fichier .txt
    Retourne une chaîne avec les informations de debug formatées
    """
    try:
        # Essayer d'obtenir quelques métadonnées clés avec exiftool
        cmd = ["exiftool", "-QuickTime:DateTimeOriginal", "-QuickTime:CreateDate", "-QuickTime:ModifyDate", "-CreateDate", "-ModifyDate", "-DateTimeOriginal", "-s", str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                return f"✅ exiftool metadata available:\n{output}"
            else:
                return "⚠️ exiftool ran successfully but no relevant metadata found"
        else:
            error_msg = result.stderr.strip() if result.stderr.strip() else "Unknown error"
            return f"❌ exiftool failed: {error_msg}"
            
    except FileNotFoundError:
        return "❌ exiftool not found - install from https://exiftool.org/"
    except subprocess.TimeoutExpired:
        return "❌ exiftool timed out (>15 seconds)"
    except Exception as e:
        return f"❌ exiftool exception: {str(e)}"

def copy_file(source: Path, dest: Path, footage_raw_path: Path, simulate=False):
    """
    Create a JSON metadata placeholder instead of copying large video files.
    This allows organization simulation without using disk space.
    """
    if simulate:
        return True
    try:
        if dest.exists():
            dest.unlink()
        
        # Create a .json placeholder instead of copying the actual video file
        json_dest = dest.with_suffix('.json')
        
        # Get debug information about time extraction
        file_mtime = datetime.fromtimestamp(source.stat().st_mtime)
        
        # Extract time from filename patterns
        filename_time = None
        import re
        filename = source.name
        
        # Pattern 1: YYYYMMDD_HHMMSS
        pattern1 = re.search(r'\d{8}_(\d{6})', filename)
        if pattern1:
            time_str = pattern1.group(1)
            h, m, s = time_str[:2], time_str[2:4], time_str[4:6]
            if 0 <= int(h) <= 23 and 0 <= int(m) <= 59 and 0 <= int(s) <= 59:
                filename_time = f"{h}:{m}:{s}"
        
        # Pattern 2: YYYYMMDDHHMMSS (14 digits total, last 6 are time)
        if not filename_time:
            pattern2 = re.search(r'(\d{14})', filename)
            if pattern2:
                full_str = pattern2.group(1)
                time_str = full_str[8:]  # Last 6 digits
                h, m, s = time_str[:2], time_str[2:4], time_str[4:6]
                if 0 <= int(h) <= 23 and 0 <= int(m) <= 59 and 0 <= int(s) <= 59:
                    filename_time = f"{h}:{m}:{s}"
        
        # Get QuickTime metadata if it's a drone file (with intelligent time selection)
        quicktime_utc = None
        quicktime_local = None
        quicktime_source = None
        time_decision_info = None
        drone_data = None
        
        if _path_has_drone_segment(source):
            drone_data = extract_times_for_drone_file(source, "America/Montreal")
            if drone_data:
                quicktime_source = drone_data["source_tag"]
                quicktime_local = drone_data["local_iso"]
                quicktime_utc = drone_data["utc_iso"]
                time_decision_info = f"Time difference: {drone_data['time_diff_minutes']:.1f} minutes from mtime"
        
        # Get video metadata for all video files
        video_metadata = extract_video_metadata(source)
        
        # Get source type information
        source_info = detect_video_source_type(source, footage_raw_path)
        
        # Execute exiftool command (unified version for consistency)
        exiftool_datetime, exiftool_result = _get_exiftool_datetime_unified(source)
        
        # Get raw metadata for debugging
        raw_ffprobe = get_raw_ffprobe_metadata(source)
        raw_exiftool = get_raw_exiftool_metadata(source)
        
        # Build structured JSON metadata
        metadata = {
            "placeholder_info": {
                "created_at": datetime.now().isoformat(),
                "original_filename": source.name,
                "original_path": str(source),
                "original_size_bytes": source.stat().st_size,
                "placeholder_format_version": "1.0"
            },
            "file_info": {
                "name": source.name,
                "extension": source.suffix.lower(),
                "size_bytes": source.stat().st_size,
                "size_mb": round(source.stat().st_size / (1024 ** 2), 2),
                "mtime": file_mtime.isoformat(),
                "mtime_readable": file_mtime.strftime('%Y-%m-%d %H:%M:%S')
            },
            "source_detection": {
                "source_type": source_info['source_type'],
                "source_tag": source_info['source_tag'],
                "device_category": source_info['device_category'],
                "is_drone_path": _path_has_drone_segment(source),
                "is_cell_path": _path_has_cell_segment(source)
            },
            "timestamps": {
                "filename_time": filename_time,
                "exiftool": {
                    "datetime": exiftool_datetime,
                    "status": exiftool_result
                }
            },
            "video_metadata": video_metadata if video_metadata else None,
            "raw_metadata": {
                "ffprobe": raw_ffprobe,
                "exiftool": raw_exiftool
            }
        }
        
        # Add drone-specific data if available
        if drone_data:
            metadata["timestamps"]["drone"] = {
                "utc_iso": quicktime_utc,
                "local_iso": quicktime_local,
                "source_tag": quicktime_source,
                "time_diff_minutes": drone_data['time_diff_minutes'],
                "decision_info": time_decision_info
            }
        
        # Write JSON with beautiful formatting
        with open(json_dest, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"[WARN] JSON placeholder creation failed: {e}")
        return False
    except Exception as e:
        print(f"[WARN] Placeholder creation failed: {e}")
        return False

def auto_link(target: Path, link_path: Path, footage_raw_path: Path, simulate=False):
    if is_windows():
        # Try hardlink first (fast, no admin)
        if create_hardlink(target, link_path, simulate):
            return True
        # Try .lnk shortcut (Windows only)
        lnk_path = link_path.with_suffix(link_path.suffix + ".lnk")
        if create_windows_lnk(target, lnk_path, simulate):
            return True
        # Final fallback: create placeholder text file
        print(f"[INFO] Creating placeholder file for: {target.name}")
        return copy_file(target, link_path, footage_raw_path, simulate)
    else:
        # On POSIX, try symlink first
        if create_symlink(target, link_path, simulate):
            return True
        # Fallback to placeholder
        print(f"[INFO] Creating placeholder file for: {target.name}")
        return copy_file(target, link_path, footage_raw_path, simulate)

def progress_line(i, total, current):
    pct = int((i / total) * 100) if total else 100
    sys.stdout.write(f"\r[{pct:3d}%] {i}/{total}  {current}")
    sys.stdout.flush()
    # Mark that a progress line was shown, so next log message will add newline
    mark_progress_line_shown()

def main():
    args = parse_args()
    
    # Handle --list-tz option
    if args.list_tz:
        list_timezones()
        sys.exit(0)
    
    # Validate required arguments
    if not args.input_dir:
        print("Error: input_dir is required")
        sys.exit(1)
    
    # Standardize project structure: expect project folder with Footage_raw inside
    project_root = args.input_dir.resolve()
    footage_raw_dir = project_root / "Footage_raw"
    
    # Validate project structure
    if not project_root.exists():
        print(f"Project directory does not exist: {project_root}")
        sys.exit(1)
    
    if not footage_raw_dir.exists():
        print(f"Footage_raw directory not found: {footage_raw_dir}")
        print("Expected project structure:")
        print(f"  {project_root}/")
        print("    Footage_raw/")
        print("      cell_blain/")
        print("      dji_drone/")
        print("      etc...")
        sys.exit(1)
    
    # Set default output_dir if not provided (standardized structure)
    if not args.output_dir:
        args.output_dir = project_root / "Footage_metadata_sorted"
        print(f"Using standardized output directory: {args.output_dir}")
    
    # Configure logging with colors
    setup_logging(level=logging.INFO)
    
    # Load time adjustments for specific groups
    time_adjustments = load_group_time_adjustments()
    
    input_root = footage_raw_dir.resolve()
    output_root = args.output_dir.resolve()

    if not input_root.exists():
        print(f"Input does not exist: {input_root}")
        sys.exit(1)

    # Determine what to process based on arguments
    process_videos = not args.photos_only
    process_photos = args.include_photos or args.photos_only
    
    # Get file lists
    if args.include_photos or args.photos_only or args.videos_only:
        all_files = list(list_media_files(input_root, 
                                        args.ext if process_videos else "", 
                                        args.photo_ext if process_photos else "",
                                        videos_only=args.videos_only,
                                        photos_only=args.photos_only))
    else:
        # Legacy mode - only videos for backward compatibility
        all_files = [(f, "video") for f in list_videos(input_root, args.ext)]
    
    total = len(all_files)
    if total == 0:
        file_type_msg = []
        if process_videos: file_type_msg.append("video")
        if process_photos: file_type_msg.append("photo") 
        print(f"No matching {' or '.join(file_type_msg)} files found.")
        return

    ensure_dir(output_root, simulate=args.simulate)

    # Always use copy mode (text placeholders)
    mode = "copy"
    created = 0
    failed = 0

    for idx, (f, file_type) in enumerate(all_files, start=1):
        # Show progress at start of iteration
        progress_line(idx, total, f.name)
        
        src = source_name(f, input_root)
        d = file_date(f, args.tz, src, time_adjustments)
        
        # Extract time and clean filename (pass timezone, group name, and time adjustments)
        time_str = extract_time_from_file(f, args.tz, src, time_adjustments)
        
        # Handle special cases
        if time_str == "KEEP_ORIGINAL":
            # No metadata time found, check if we should use mtime or date_non_valide
            # Create type-specific root folder (photo or video)
            type_root = output_root / ("photo" if file_type == "photo" else "video")
            
            # Check if filename contains "dji" or "DJI" (case-insensitive)
            has_dji_in_name = "dji" in f.name.lower()
            
            if has_dji_in_name and d is not None:
                # DJI file with valid mtime - use it (likely drone footage with correct file time)
                day_dir = type_root / d.strftime("%Y-%m-%d")
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                # Apply time adjustment if configured
                if time_adjustments and src:
                    mtime_adjusted = adjust_datetime_for_group(mtime, src, time_adjustments)
                else:
                    mtime_adjusted = mtime
                time_str = f"{mtime_adjusted.hour:02d}h{mtime_adjusted.minute:02d}m{mtime_adjusted.second:02d}s"
                clean_name = remove_temporal_elements(f.name, file_type)
                out_name = f"{time_str}_{src}_{clean_name}"
                logging.info(f"📷 Using mtime for DJI file {f.name} (no metadata found)")
            else:
                # Not DJI or no valid date - put in date_non_valide (mtime unreliable)
                day_dir = type_root / "date_non_valide"
                original_name = f.name
                out_name = f"{src}_{original_name}"
                logging.warning(f"⚠️  No metadata for {f.name} - placed in date_non_valide")
        elif time_str is None:
            # File doesn't have valid time info, put in date_non_valide
            # Create type-specific root folder (photo or video)
            type_root = output_root / ("photo" if file_type == "photo" else "video")
            day_dir = type_root / "date_non_valide"
            time_str = "00h00m00s"  # Default time for invalid files
            d = None  # Override date to ensure it goes to date_non_valide
            clean_name = remove_temporal_elements(f.name, file_type)
            out_name = f"{time_str}_{src}_{clean_name}"
        else:
            # Normal processing
            # Create type-specific root folder (photo or video)
            type_root = output_root / ("photo" if file_type == "photo" else "video")
            
            # Handle invalid dates
            if d is None:
                day_dir = type_root / "date_non_valide"
            else:
                day_dir = type_root / d.strftime("%Y-%m-%d")
                
            clean_name = remove_temporal_elements(f.name, file_type)
            # New naming format: <heure>_<sous-dossier>_<nom_original_sans_temps>
            out_name = f"{time_str}_{src}_{clean_name}"
        
        ensure_dir(day_dir, simulate=args.simulate)
        out_path = day_dir / out_name

        # Ensure uniqueness
        out_path = unique_path(out_path)

        # Create link
        ok = False
        if mode == "auto":
            ok = auto_link(f, out_path, footage_raw_dir, simulate=args.simulate)
        elif mode == "symlink":
            ok = create_symlink(f, out_path, simulate=args.simulate)
        elif mode == "hardlink":
            ok = create_hardlink(f, out_path, simulate=args.simulate)
        elif mode == "winlnk":
            # Ensure .lnk ext for clarity
            if out_path.suffix.lower() != ".lnk":
                out_path = out_path.with_suffix(out_path.suffix + ".lnk")
            ok = create_windows_lnk(f, out_path, simulate=args.simulate)
        elif mode == "copy":
            ok = copy_file(f, out_path, footage_raw_dir, simulate=args.simulate)
        else:
            print(f"[ERR] Unknown link mode: {mode}")
            sys.exit(2)

        created += 1 if ok else 0
        failed  += 0 if ok else 1

        # Progress line already shown at start of iteration

    # Final newline after progress
    print()
    print(f"Done. Created: {created}, Failed: {failed}, Total: {total}")
    if args.simulate:
        print("[SIMULATE] No changes were written. Re-run without --simulate to apply.")

def test_montreal_timezone():
    """Test unitaire: vérifier que America/Montreal applique -04:00 en été et -05:00 en hiver"""
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo("America/Montreal")
        
        # Test été (juillet) - devrait être -04:00 (EDT)
        summer_utc = datetime(2025, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
        summer_local = summer_utc.astimezone(tz)
        summer_offset = summer_local.strftime("%z")
        assert summer_offset == "-0400", f"Expected -0400 in summer, got {summer_offset}"
        
        # Test hiver (janvier) - devrait être -05:00 (EST)  
        winter_utc = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        winter_local = winter_utc.astimezone(tz)
        winter_offset = winter_local.strftime("%z")
        assert winter_offset == "-0500", f"Expected -0500 in winter, got {winter_offset}"
        
        print("✓ Tests timezone Montreal: OK (été -04:00, hiver -05:00)")
        
    except Exception as e:
        print(f"✗ Tests timezone Montreal échoués: {e}")

def test_drone_segment_detection():
    """Test unitaire: vérifier la détection du segment 'drone'"""
    from pathlib import Path
    
    # Cas positifs
    assert _path_has_drone_segment(Path("/videos/drone/DJI_123.mp4"))
    assert _path_has_drone_segment(Path("C:/footage/DRONE/video.mov"))
    assert _path_has_drone_segment(Path("./data/Drone/clip.mp4"))
    
    # Cas négatifs 
    assert not _path_has_drone_segment(Path("/videos/mydrone/clip.mp4"))
    assert not _path_has_drone_segment(Path("/dronevideos/clip.mp4"))
    assert not _path_has_drone_segment(Path("/videos/cell_blain/clip.mp4"))
    
    print("✓ Tests détection segment drone: OK")

if __name__ == "__main__":
    # Si appelé avec --test, lancer les tests
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_montreal_timezone()
        test_drone_segment_detection()
        sys.exit(0)
        
    main()
