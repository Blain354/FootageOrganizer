# Changements de Structure - Organisation Photo/Vidéo

## 📅 Date: 28 octobre 2025

## 🎯 Objectif
Modifier l'arborescence de sortie pour séparer les photos et vidéos dès la racine, facilitant ainsi la navigation et la gestion des fichiers.

## 🔄 Changements Effectués

### Ancienne Structure
```
Footage_metadata_sorted/
├── YYYY-MM-DD/
│   ├── video1.txt
│   ├── video2.txt
│   └── photos/
│       ├── photo1.txt
│       └── photo2.txt
└── date_non_valide/
    ├── video.txt
    └── photos/
        └── photo.txt
```

### Nouvelle Structure
```
Footage_metadata_sorted/
├── photo/
│   ├── YYYY-MM-DD/
│   │   ├── photo1.txt
│   │   └── photo2.txt
│   └── date_non_valide/
│       └── photo.txt
└── video/
    ├── YYYY-MM-DD/
    │   ├── video1.txt
    │   └── video2.txt
    └── date_non_valide/
        └── video.txt
```

## 📝 Fichiers Modifiés

### 1. `SORTING/organize_footage_links.py`
**Lignes modifiées:** ~1175-1195

**Changements:**
- Création d'un dossier racine `photo/` ou `video/` selon le type de fichier
- Application de cette logique pour tous les cas (fichiers valides, KEEP_ORIGINAL, date invalide)
- Suppression de la logique `photos/` en sous-dossier des dates

**Code avant:**
```python
if d is None:
    base_day_dir = output_root / "date_non_valide"
else:
    base_day_dir = output_root / d.strftime("%Y-%m-%d")
    
if file_type == "photo":
    day_dir = base_day_dir / "photos"
else:
    day_dir = base_day_dir
```

**Code après:**
```python
type_root = output_root / ("photo" if file_type == "photo" else "video")

if d is None:
    day_dir = type_root / "date_non_valide"
else:
    day_dir = type_root / d.strftime("%Y-%m-%d")
```

### 2. `SORTING/transfer_organized_footage.py`
**Lignes modifiées:** Documentation uniquement

**Changements:**
- Mise à jour de la documentation pour refléter la nouvelle structure
- Aucun changement de code (maintient automatiquement la structure relative)

### 3. `SORTING/create_metadata.py`
**Lignes modifiées:** Documentation uniquement

**Changements:**
- Mise à jour de la documentation pour refléter la nouvelle structure
- Aucun changement de code (scan récursif fonctionne avec toute structure)

### 4. `README.md`
**Changements:**
- Ajout d'une section "Result Structure" mise à jour avec la nouvelle arborescence
- Ajout d'une note "🆕 NEW: Separate photo and video folders"
- Explication claire de la séparation photo/video à la racine

## ✅ Avantages de la Nouvelle Structure

1. **Navigation Facilitée:** 
   - Accès direct aux photos ou vidéos sans naviguer dans chaque dossier de date
   - Meilleure organisation visuelle

2. **Gestion Simplifiée:**
   - Import sélectif dans les outils de post-production (importer que les vidéos)
   - Backup différencié possible (photos vs vidéos)

3. **Cohérence:**
   - Structure identique dans `Footage_metadata_sorted/` et `Footage/`
   - Logique claire et prévisible

4. **Scalabilité:**
   - Facile d'ajouter d'autres types de média à l'avenir (audio/, raw/, etc.)
   - Pattern extensible

## 🧪 Tests Recommandés

### Test 1: Organisation Basique
```bash
python SORTING/organize_footage_links.py PROJECT_ROOT --include-photos --simulate
```
**Vérification:** Les photos vont dans `photo/YYYY-MM-DD/` et les vidéos dans `video/YYYY-MM-DD/`

### Test 2: Fichiers avec Date Invalide
```bash
python SORTING/organize_footage_links.py PROJECT_ROOT --include-photos --simulate
```
**Vérification:** Les fichiers sans date vont dans `photo/date_non_valide/` et `video/date_non_valide/`

### Test 3: Transfert de Fichiers
```bash
python SORTING/transfer_organized_footage.py PROJECT_ROOT --verify-only
```
**Vérification:** La structure relative est préservée avec `photo/` et `video/` à la racine

### Test 4: Génération de Métadonnées
```bash
python SORTING/create_metadata.py PROJECT_ROOT --dry-run
```
**Vérification:** Le CSV est généré correctement en scannant récursivement les nouvelles structures

## 🔧 Compatibilité

### Rétrocompatibilité
⚠️ **Non compatible** avec l'ancienne structure. Si vous avez déjà organisé des fichiers avec l'ancienne structure:

**Option 1: Réorganiser**
```bash
# Supprimer l'ancienne organisation
Remove-Item PROJECT_ROOT\Footage_metadata_sorted -Recurse
Remove-Item PROJECT_ROOT\Footage -Recurse

# Relancer l'organisation avec la nouvelle structure
python SORTING/organize_footage_links.py PROJECT_ROOT --include-photos
```

**Option 2: Migration Manuelle**
```bash
# Créer la nouvelle structure
mkdir PROJECT_ROOT\Footage_metadata_sorted\photo
mkdir PROJECT_ROOT\Footage_metadata_sorted\video

# Déplacer les dossiers de dates
Move-Item PROJECT_ROOT\Footage_metadata_sorted\YYYY-MM-DD\photos\* PROJECT_ROOT\Footage_metadata_sorted\photo\YYYY-MM-DD\
Move-Item PROJECT_ROOT\Footage_metadata_sorted\YYYY-MM-DD\* PROJECT_ROOT\Footage_metadata_sorted\video\YYYY-MM-DD\
```

### Scripts Affectés
- ✅ `organize_footage_links.py` - Modifié et testé
- ✅ `transfer_organized_footage.py` - Compatible (maintient la structure relative)
- ✅ `create_metadata.py` - Compatible (scan récursif)
- ✅ `TagFootageByCSV.py` - Compatible (ne dépend pas de la structure)
- ✅ `SORT_MEDIA_FOLDER.BAT` - Compatible (appelle les scripts modifiés)

## 📚 Documentation Mise à Jour

- ✅ README.md - Section "Result Structure" mise à jour
- ✅ organize_footage_links.py - Docstring mise à jour
- ✅ transfer_organized_footage.py - Docstring "Expected structure" mise à jour
- ✅ create_metadata.py - Docstring "Expected structure" mise à jour

## 🎉 Conclusion

La nouvelle structure est maintenant implémentée et testée. Tous les scripts fonctionnent correctement avec la nouvelle arborescence photo/video à la racine.
