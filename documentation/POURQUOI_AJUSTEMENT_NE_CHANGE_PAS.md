# 🔄 Pourquoi l'Ajustement ne Change Pas?

## 📅 Date: 28 octobre 2025

## ❓ Question

> "Pourquoi le footage nommé DJI_... dans le dossier avata ne change pas lorsque je change l'ajustement lié au groupe avata?"

## ✅ Réponse: Fichiers Existants

Les fichiers JSON placeholders ont **déjà été créés** avec l'ancienne configuration. Quand vous changez `specific_group_time_adjust.json`, les fichiers existants **ne sont PAS automatiquement mis à jour**.

## 🔍 Ordre des Opérations

### Ce qui se passe à l'exécution

```
1. Script lit specific_group_time_adjust.json
2. Pour chaque fichier:
   - Extrait date/heure
   - Applique ajustement selon groupe
   - Crée nom de fichier: {heure}_{groupe}_{nom}.json
   - SI le fichier .json existe DÉJÀ → SKIP (pas de recréation)
   - SI le fichier .json n'existe pas → Crée nouveau
```

**Le problème**: Si `14h30m00s_avata_DJI_0001.json` existe déjà, le script le **garde tel quel** même si vous changez l'ajustement à +6h (qui devrait donner `20h30m00s_avata_DJI_0001.json`).

## 🛠️ Solution: Supprimer et Régénérer

### Méthode 1: Supprimer Tout et Régénérer

**PowerShell**:
```powershell
# Supprimer le dossier d'organisation complet
Remove-Item "F:\path\to\projet\Footage_metadata_sorted" -Recurse -Force

# Relancer l'organisation
.\SORT_MEDIA_FOLDER.BAT "F:\path\to\projet"
```

**Résultat**: Tous les fichiers JSON seront recréés avec le nouvel ajustement.

### Méthode 2: Supprimer Seulement le Groupe Avata

**PowerShell**:
```powershell
# Naviguer dans video/ et photo/
cd "F:\path\to\projet\Footage_metadata_sorted\video"

# Supprimer tous les fichiers contenant _avata_
Get-ChildItem -Recurse -Filter "*_avata_*" | Remove-Item -Force

cd "..\photo"
Get-ChildItem -Recurse -Filter "*_avata_*" | Remove-Item -Force

# Relancer l'organisation
cd F:\Utils\script_triage\SORTING
.\SORT_MEDIA_FOLDER.BAT "F:\path\to\projet"
```

**Résultat**: Seuls les fichiers Avata seront recréés.

### Méthode 3: Modification du Script (Force Overwrite)

Si vous voulez **toujours écraser** les fichiers existants, vous devez modifier le script.

**À FAIRE**: Dans `organize_footage_links.py`, ligne ~1495, modifier:

```python
# AVANT (ligne 1495):
out_path = unique_path(out_path)

# APRÈS (force overwrite):
# out_path = unique_path(out_path)  # Commenté pour forcer écrasement
if out_path.exists():
    out_path.unlink()  # Supprime l'ancien fichier
```

**⚠️ Attention**: Cette modification ralentira l'exécution car tous les fichiers seront recréés à chaque fois.

## 📊 Exemple Concret

### Situation

**Dossier**: `Footage_raw/avata/DJI_0001.MP4`  
**mtime**: `2024-10-15 14:30:00`

### Configuration Initiale

```json
{
    "avata": "+00000000_040000"
}
```

**1ère Exécution**:
```
14:30 + 4h = 18:30
Crée: video/2024-10-15/18h30m00s_avata_DJI_0001.json
```

### Changement de Configuration

```json
{
    "avata": "+00000000_060000"
}
```

**2e Exécution SANS supprimer**:
```
Le fichier 18h30m00s_avata_DJI_0001.json existe déjà
→ SKIP (pas de modification)
```

**2e Exécution APRÈS suppression**:
```
14:30 + 6h = 20:30
Crée: video/2024-10-15/20h30m00s_avata_DJI_0001.json ✅
```

## 🔍 Vérification

### Voir le Contenu du JSON

```powershell
# Ouvrir le JSON dans notepad
notepad "F:\path\to\projet\Footage_metadata_sorted\video\2024-10-15\18h30m00s_avata_DJI_0001.json"
```

**Regarder**:
```json
{
    "file_info": {
        "mtime_readable": "2024-10-15 14:30:00"
    }
}
```

Si le mtime est `14:30` mais le nom du fichier est `18h30m00s`, alors l'ajustement de +4h a été appliqué.

Si vous voulez +6h, le fichier devrait s'appeler `20h30m00s` et il faut le **régénérer**.

## 💡 Workflow Recommandé

### 1. Tester d'Abord avec un Groupe

```json
{
    "avata_test": "+00000000_060000"
}
```

Créez un dossier `Footage_raw/avata_test/` avec un fichier test.

### 2. Exécuter et Vérifier

```powershell
.\SORT_MEDIA_FOLDER.BAT "F:\path\to\projet"
```

Vérifiez que l'heure dans le nom de fichier correspond.

### 3. Appliquer à Tous les Avata

Une fois satisfait, renommez le groupe dans le JSON:

```json
{
    "avata": "+00000000_060000"
}
```

Et **supprimez les anciens fichiers**:
```powershell
Remove-Item "F:\path\to\projet\Footage_metadata_sorted\video\*\*_avata_*" -Force
Remove-Item "F:\path\to\projet\Footage_metadata_sorted\photo\*\*_avata_*" -Force
```

Puis relancez le script.

## ⚙️ Configuration Actuelle

Votre `specific_group_time_adjust.json`:
```json
{
    "canon": "+00000001_000000",
    "safari6d": "-00000000_040000",
    "avata": "+00000000_060000"
}
```

**Avata**: +6 heures (changé récemment)

**Pour appliquer**: Supprimez les fichiers Avata existants et relancez!

## 📋 Résumé

| Action | Effet sur Fichiers Existants |
|--------|------------------------------|
| Modifier `specific_group_time_adjust.json` | ❌ Aucun effet (fichiers gardés) |
| Relancer script sans supprimer | ❌ Fichiers existants skippés |
| Supprimer fichiers PUIS relancer | ✅ Fichiers recréés avec nouvel ajustement |
| Modifier script pour forcer overwrite | ✅ Tous fichiers toujours recréés (lent) |

---

**Date**: 28 octobre 2025  
**Réponse**: Les fichiers JSON ne sont pas automatiquement mis à jour  
**Solution**: Supprimer les fichiers Avata existants et relancer le script
