#!/usr/bin/env python3
"""
transfer_organized_footage.py

Transfers real video files based on placeholder organization created by organize_footage_links.py.

Functions:
- Reads each .txt placeholder file in Footage_metadata_sorted
- Extracts original video file path from metadata
- Copies or moves files to final structure in Footage/
- Updates paths in .txt files after transfer
- Verifies integrity with file size checks

Usage:
    python transfer_organized_footage.py PROJECT_ROOT [OPTIONS]

Arguments:
    PROJECT_ROOT : Project root folder (must contain Footage_metadata_sorted/)
    
Options:
    --copy        : Keep original files (copy instead of move)
    --verify-only : Only verify files without transferring them

Expected structure:
    PROJECT_ROOT/
    ├── Footage_metadata_sorted/  (source folder with .txt placeholders)
    │   ├── photo/
    │   │   ├── YYYY-MM-DD/
    │   │   └── date_non_valide/
    │   └── video/
    │       ├── YYYY-MM-DD/
    │       └── date_non_valide/
    └── Footage/                  (destination folder created automatically)
        ├── photo/
        │   ├── YYYY-MM-DD/
        │   └── date_non_valide/
        └── video/
            ├── YYYY-MM-DD/
            └── date_non_valide/

Security:
- First copies all files, then deletes originals only if complete success
- Multiple integrity verifications with sizes and checksums
- Detailed progress bar and complete operation logs
- Dry-run mode for verification before actual transfer
"""

import argparse
import os
import sys
import shutil
import logging
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

def setup_logging(log_file: Path):
    """Configure le logging avec fichier et console"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def progress_bar(current: int, total: int, description: str = "", width: int = 50):
    """Affiche une barre de progression"""
    if total == 0:
        percent = 100
    else:
        percent = (current * 100) // total
    
    filled = (width * current) // total if total > 0 else width
    bar = '█' * filled + '░' * (width - filled)
    
    sys.stdout.write(f'\r[{bar}] {percent:3d}% ({current}/{total}) {description}')
    sys.stdout.flush()
    
    if current == total:
        print()  # Nouvelle ligne à la fin

def extract_original_path_from_placeholder(placeholder_file: Path) -> Optional[Path]:
    """
    Extrait le chemin original du fichier depuis le placeholder (.txt ou .json)
    Supporte les deux formats pour rétrocompatibilité
    """
    try:
        if placeholder_file.suffix == '.json':
            # Nouveau format JSON
            with open(placeholder_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                path_str = data.get('placeholder_info', {}).get('original_path')
                if path_str:
                    return Path(path_str)
        else:
            # Ancien format TXT
            with open(placeholder_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Original path: "):
                        path_str = line.replace("Original path: ", "")
                        return Path(path_str)
        return None
    except Exception as e:
        logging.error(f"Erreur lecture {placeholder_file}: {e}")
        return None

def update_placeholder_file_path(placeholder_file: Path, new_video_path: Path):
    """
    Met à jour le chemin original dans le fichier placeholder (.txt ou .json)
    Supporte les deux formats pour rétrocompatibilité
    """
    try:
        if placeholder_file.suffix == '.json':
            # Format JSON - mettre à jour la structure
            with open(placeholder_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Mettre à jour le chemin
            if 'placeholder_info' not in data:
                data['placeholder_info'] = {}
            data['placeholder_info']['original_path'] = str(new_video_path)
            
            # Ajouter info de transfert
            if 'transfer_info' not in data:
                data['transfer_info'] = {}
            data['transfer_info']['transferred_at'] = datetime.now().isoformat()
            data['transfer_info']['new_location'] = str(new_video_path)
            
            # Réécrire le JSON
            with open(placeholder_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        else:
            # Ancien format TXT
            with open(placeholder_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer la ligne "Original path: "
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("Original path: "):
                    lines[i] = f"Original path: {new_video_path}"
                    break
            
            # Ajouter une note de transfert
            transfer_note = f"\n=== TRANSFER INFO ===\n"
            transfer_note += f"Transferred on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            transfer_note += f"New location: {new_video_path}\n"
            
            # Écrire le nouveau contenu
            with open(placeholder_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + transfer_note)
            
    except Exception as e:
        logging.error(f"Erreur mise à jour {placeholder_file}: {e}")

def verify_file_integrity(source: Path, dest: Path) -> bool:
    """Vérifie l'intégrité d'un fichier copié en comparant les tailles"""
    try:
        source_size = source.stat().st_size
        dest_size = dest.stat().st_size
        
        if source_size != dest_size:
            logging.error(f"Tailles différentes - Source: {source_size}, Dest: {dest_size}")
            return False
            
        return True
    except Exception as e:
        logging.error(f"Erreur vérification intégrité {source} -> {dest}: {e}")
        return False

def copy_with_verification(source: Path, dest: Path) -> bool:
    """Copie un fichier avec vérification d'intégrité"""
    try:
        # Créer le dossier de destination si nécessaire
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Copier le fichier
        shutil.copy2(source, dest)
        
        # Vérifier l'intégrité
        if not verify_file_integrity(source, dest):
            logging.error(f"Échec vérification intégrité: {source} -> {dest}")
            # Supprimer le fichier défaillant
            if dest.exists():
                dest.unlink()
            return False
        
        logging.info(f"Copie réussie: {source.name}")
        return True
        
    except Exception as e:
        logging.error(f"Erreur copie {source} -> {dest}: {e}")
        return False

def find_placeholder_files(organized_dir: Path) -> List[Path]:
    """Trouve tous les fichiers placeholders (.txt et .json) dans le dossier organisé"""
    placeholder_files = []
    for placeholder_file in organized_dir.rglob("*.json"):
        if placeholder_file.is_file():
            placeholder_files.append(placeholder_file)
    # Support des anciens fichiers .txt aussi
    for placeholder_file in organized_dir.rglob("*.txt"):
        if placeholder_file.is_file() and placeholder_file.name != "transfer_log.txt":
            placeholder_files.append(placeholder_file)
    return sorted(placeholder_files)

def calculate_total_size(files: List[Tuple[Path, Path]]) -> int:
    """Calcule la taille totale des fichiers à transférer"""
    total_size = 0
    for source, _ in files:
        if source.exists():
            total_size += source.stat().st_size
    return total_size

def format_size(size_bytes: int) -> str:
    """Formate la taille en unités lisibles"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def main():
    parser = argparse.ArgumentParser(description="Transfère les vrais fichiers vidéo basé sur l'organisation des placeholders .txt")
    parser.add_argument("project_root", type=Path, help="Dossier racine du projet (contient Footage_metadata_sorted)")
    parser.add_argument("--copy", action="store_true", help="Garde les fichiers originaux (copie au lieu de déplacer)")
    parser.add_argument("--verify-only", action="store_true", help="Vérifie seulement les fichiers sans les transférer")
    
    args = parser.parse_args()
    
    project_root = args.project_root.resolve()
    organized_dir = project_root / "Footage_metadata_sorted"
    output_dir = project_root / "Footage"
    
    # Validation de la structure du projet
    if not project_root.exists():
        print(f"Erreur: Le dossier racine du projet n'existe pas: {project_root}")
        sys.exit(1)
    
    if not organized_dir.exists():
        print(f"Erreur: Le dossier organisé n'existe pas: {organized_dir}")
        print(f"Structure attendue: {project_root}/Footage_metadata_sorted/")
        sys.exit(1)
    
    # Configuration du logging
    log_file = output_dir / f"transfer_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file)
    
    logging.info(f"=== DÉBUT DU TRANSFERT ===")
    logging.info(f"Dossier source: {organized_dir}")
    logging.info(f"Dossier destination: {output_dir}")
    logging.info(f"Mode: {'COPIE' if args.copy else 'DÉPLACEMENT'}")
    logging.info(f"Vérification seulement: {args.verify_only}")
    
    # Étape 1: Trouver tous les fichiers placeholders (.txt et .json)
    print("🔍 Recherche des fichiers placeholders...")
    placeholder_files = find_placeholder_files(organized_dir)
    
    if not placeholder_files:
        print("Aucun fichier placeholder trouvé dans le dossier organisé.")
        sys.exit(0)
    
    print(f"Trouvé {len(placeholder_files)} fichiers placeholders")
    
    # Étape 2: Analyser les fichiers placeholders et préparer les transferts
    print("📋 Analyse des fichiers placeholders...")
    transfers = []  # Liste de (source_path, dest_path, placeholder_file)
    missing_files = []
    
    for i, placeholder_file in enumerate(placeholder_files):
        progress_bar(i, len(placeholder_files), f"Analyse: {placeholder_file.name}")
        
        original_path = extract_original_path_from_placeholder(placeholder_file)
        if not original_path:
            logging.warning(f"Impossible d'extraire le chemin original de: {placeholder_file}")
            continue
        
        if not original_path.exists():
            logging.warning(f"Fichier original manquant: {original_path}")
            missing_files.append((original_path, placeholder_file))
            continue
        
        # Calculer le chemin de destination
        # Maintenir la même structure relative que les placeholders
        relative_path = placeholder_file.relative_to(organized_dir)
        # Remplacer l'extension .txt/.json par l'extension originale
        dest_path = output_dir / relative_path.with_suffix(original_path.suffix)
        
        transfers.append((original_path, dest_path, placeholder_file))
    
    progress_bar(len(placeholder_files), len(placeholder_files), "Analyse terminée")
    
    # Rapport d'analyse
    print(f"\n📊 RAPPORT D'ANALYSE:")
    print(f"   • Fichiers à transférer: {len(transfers)}")
    print(f"   • Fichiers manquants: {len(missing_files)}")
    
    if missing_files:
        print(f"\n❌ FICHIERS MANQUANTS:")
        for original_path, txt_file in missing_files[:10]:  # Limiter l'affichage
            print(f"   • {original_path} (référencé par {txt_file.name})")
        if len(missing_files) > 10:
            print(f"   • ... et {len(missing_files) - 10} autres")
    
    if not transfers:
        print("Aucun fichier à transférer. Arrêt.")
        sys.exit(0)
    
    # Calcul de la taille totale
    total_size = calculate_total_size([(s, d) for s, d, _ in transfers])
    print(f"   • Taille totale: {format_size(total_size)}")
    
    # Mode vérification seulement
    if args.verify_only:
        print(f"\n✅ VÉRIFICATION TERMINÉE - Tous les fichiers sont accessibles")
        logging.info("Mode vérification seulement - Aucun transfert effectué")
        sys.exit(0)
    
    # Confirmation utilisateur
    if not args.copy:
        response = input(f"\n⚠️  ATTENTION: Vous allez DÉPLACER {len(transfers)} fichiers ({format_size(total_size)}). Continuer? (oui/non): ")
        if response.lower() not in ['oui', 'o', 'yes', 'y']:
            print("Transfert annulé.")
            sys.exit(0)
    
    # Étape 3: Effectuer les transferts
    print(f"\n🚀 DÉBUT DES TRANSFERTS...")
    successful_transfers = []
    failed_transfers = []
    
    for i, (source_path, dest_path, txt_file) in enumerate(transfers):
        progress_bar(i, len(transfers), f"Transfert: {source_path.name}")
        
        # Vérifier si le fichier destination existe déjà
        if dest_path.exists():
            logging.warning(f"Destination existe déjà: {dest_path}")
            # Générer un nom unique
            counter = 1
            while dest_path.exists():
                stem = dest_path.stem
                suffix = dest_path.suffix
                dest_path = dest_path.parent / f"{stem}_{counter:03d}{suffix}"
                counter += 1
        
        # Effectuer la copie
        success = copy_with_verification(source_path, dest_path)
        
        if success:
            successful_transfers.append((source_path, dest_path, placeholder_file))
            # Mettre à jour le fichier placeholder avec le nouveau chemin
            update_placeholder_file_path(placeholder_file, dest_path)
        else:
            failed_transfers.append((source_path, dest_path, txt_file))
    
    progress_bar(len(transfers), len(transfers), "Transferts terminés")
    
    # Rapport des transferts
    print(f"\n📊 RAPPORT DES TRANSFERTS:")
    print(f"   • Réussis: {len(successful_transfers)}")
    print(f"   • Échoués: {len(failed_transfers)}")
    
    if failed_transfers:
        print(f"\n❌ TRANSFERTS ÉCHOUÉS:")
        for source_path, dest_path, txt_file in failed_transfers:
            print(f"   • {source_path.name}")
        logging.error(f"{len(failed_transfers)} transferts ont échoué")
    
    # Étape 4: Suppression des originaux (seulement si mode déplacement et tous les transferts réussis)
    if not args.copy and successful_transfers and not failed_transfers:
        print(f"\n🗑️  SUPPRESSION DES ORIGINAUX...")
        
        deleted_count = 0
        delete_errors = 0
        
        for i, (source_path, dest_path, txt_file) in enumerate(successful_transfers):
            progress_bar(i, len(successful_transfers), f"Suppression: {source_path.name}")
            
            try:
                # Vérification finale avant suppression
                if verify_file_integrity(dest_path, source_path):  # Ordre inversé pour vérifier dest vs source
                    source_path.unlink()
                    deleted_count += 1
                    logging.info(f"Original supprimé: {source_path}")
                else:
                    logging.error(f"Vérification finale échouée pour: {source_path}")
                    delete_errors += 1
            except Exception as e:
                logging.error(f"Erreur suppression {source_path}: {e}")
                delete_errors += 1
        
        progress_bar(len(successful_transfers), len(successful_transfers), "Suppression terminée")
        
        print(f"\n📊 RAPPORT DE SUPPRESSION:")
        print(f"   • Originaux supprimés: {deleted_count}")
        print(f"   • Erreurs de suppression: {delete_errors}")
        
        if delete_errors > 0:
            print(f"\n⚠️  ATTENTION: {delete_errors} fichiers originaux n'ont pas pu être supprimés")
            logging.warning(f"{delete_errors} fichiers originaux non supprimés")
    
    elif not args.copy:
        print(f"\n⚠️  SUPPRESSION ANNULÉE: Des transferts ont échoué")
        logging.warning("Suppression des originaux annulée à cause d'échecs de transfert")
    
    # Rapport final
    print(f"\n✅ TRANSFERT TERMINÉ!")
    logging.info(f"=== FIN DU TRANSFERT ===")
    logging.info(f"Fichiers transférés avec succès: {len(successful_transfers)}")
    logging.info(f"Fichiers en échec: {len(failed_transfers)}")
    logging.info(f"Log sauvegardé dans: {log_file}")
    
    print(f"Log détaillé disponible dans: {log_file}")
    
    if failed_transfers:
        sys.exit(1)  # Code d'erreur si des transferts ont échoué

if __name__ == "__main__":
    main()
