# Ajustement Temporel par Groupe

## 📅 Date: 28 octobre 2025

## 🎯 Objectif

Permettre d'ajuster manuellement la date/heure d'acquisition pour des groupes spécifiques de fichiers, afin de corriger des décalages causés par:
- Mauvais réglage d'horloge sur l'appareil
- Changement de fuseau horaire non pris en compte
- Erreur de configuration de date/heure

## 📋 Configuration

### Fichier de Configuration

**Nom**: `specific_group_time_adjust.json`  
**Emplacement**: Racine du projet (même niveau que `SORTING/`)

**Format**:
```json
{
    "nom_groupe": "[+/-]YYYYMMDD_HHMMSS",
    "canon": "+00000001_000000",
    "gopro": "-00000000_020000"
}
```

### Format du Delta

Le format est: `[+/-]YYYYMMDD_HHMMSS`

**Composantes**:
- `+` ou `-` : Ajouter ou soustraire le temps
- `YYYY` : Années (0000-9999)
- `MM` : Mois (00-99, approximé à 30 jours)
- `DD` : Jours (00-99)
- `_` : Séparateur
- `HH` : Heures (00-23)
- `MM` : Minutes (00-59)
- `SS` : Secondes (00-59)

**Exemples**:

| Delta | Description | Effet |
|-------|-------------|-------|
| `+00000001_000000` | Ajouter 1 jour | Date + 1 jour |
| `-00000001_000000` | Soustraire 1 jour | Date - 1 jour |
| `+00000000_020000` | Ajouter 2 heures | Heure + 2h (rollover si nécessaire) |
| `-00000000_010000` | Soustraire 1 heure | Heure - 1h |
| `+00000100_000000` | Ajouter 1 mois | Date + 30 jours |
| `+00010000_000000` | Ajouter 1 an | Date + 365 jours |
| `+00000000_000030` | Ajouter 30 secondes | Heure + 30s |

## 🔧 Fonctionnement

### 1. Chargement de la Configuration

Au démarrage, le script charge automatiquement `specific_group_time_adjust.json`:

```python
time_adjustments = load_group_time_adjustments()
# Logs: ⏰ Loaded time adjustments for N group(s)
```

### 2. Application de l'Ajustement

Pour chaque fichier traité:

1. **Extraction de la date/heure** depuis les métadonnées (exiftool, ffprobe, filename)
2. **Identification du groupe** (dossier source sous `Footage_raw/`)
3. **Vérification** si le groupe a un ajustement configuré
4. **Application du delta** si configuré
5. **Logging** de l'opération

```python
def file_date(p: Path, tz_name, group_name, time_adjustments):
    # Extract datetime from metadata
    dt = extract_datetime_from_file(p)
    
    # Apply adjustment if configured for this group
    if group_name in time_adjustments:
        adjusted_dt = apply_time_delta(dt, time_adjustments[group_name])
        return adjusted_dt.date()
    
    return dt.date()
```

### 3. Gestion du Rollover Temporel

Le système gère automatiquement les débordements temporels:

**Exemple 1**: Vidéo à 23h + 2h d'ajustement
```
Original:  2024-10-15 23:00:00
Delta:     +00000000_020000
Adjusted:  2024-10-16 01:00:00  ← Passe au jour suivant!
```

**Exemple 2**: Vidéo le 31 décembre + 1 jour
```
Original:  2024-12-31 12:00:00
Delta:     +00000001_000000
Adjusted:  2025-01-01 12:00:00  ← Passe à l'année suivante!
```

**Exemple 3**: Soustraction d'heure
```
Original:  2024-10-16 01:00:00
Delta:     -00000000_020000
Adjusted:  2024-10-15 23:00:00  ← Retour au jour précédent!
```

## 📊 Exemple d'Utilisation

### Scénario: Canon avec horloge en retard d'un jour

#### Configuration

Créer `specific_group_time_adjust.json`:
```json
{
    "canon": "+00000001_000000"
}
```

#### Structure des Fichiers

```
Footage_raw/
  canon/
    IMG_1234.MOV  (métadonnées: 2024-10-14 14:30:00)
    IMG_1235.MOV  (métadonnées: 2024-10-14 16:45:00)
```

#### Traitement

```bash
python SORTING/organize_footage_links.py project_folder
```

#### Logs

```
INFO: ⏰ Loaded time adjustments for 1 group(s) from specific_group_time_adjust.json
...
INFO: ⏰ Applied time adjustment to group 'canon': +00000001_000000
DEBUG:    Original: 2024-10-14 14:30:00
DEBUG:    Adjusted: 2024-10-15 14:30:00
INFO: 📅 Using metadata date for IMG_1234.MOV: 2024-10-15
```

#### Résultat

```
Footage_metadata_sorted/
  video/
    2024-10-15/               ← Date ajustée!
      14h30m00s_canon_IMG_1234.json
      16h45m00s_canon_IMG_1235.json
```

Sans ajustement, les fichiers auraient été dans `2024-10-14/`.

## 🧪 Tests

### Script de Test

Un script de test valide les fonctions d'ajustement:

```bash
python test_time_adjustment.py
```

**Tests effectués**:
1. ✅ Parsing des deltas (format validation)
2. ✅ Application des deltas (calculs temporels)
3. ✅ Rollover de jour (23h + 2h → 1h jour suivant)
4. ✅ Rollover d'année (31 déc → 1er jan)
5. ✅ Soustraction d'heures
6. ✅ Ajustement du groupe Canon (+1 jour)

### Résultats Attendus

```
Testing Canon Group Adjustment (+1 day)
============================================================

Original:  2024-10-15 00:00:00
Adjusted:  2024-10-16 00:00:00
Date only: 2024-10-16

Original:  2024-10-15 12:00:00
Adjusted:  2024-10-16 12:00:00
Date only: 2024-10-16

Original:  2024-10-15 23:59:59
Adjusted:  2024-10-16 23:59:59
Date only: 2024-10-16
```

## 🔍 Fonctions Ajoutées

### `parse_time_delta(delta_str) -> Tuple[int, int]`

Parse une chaîne de delta temporel.

**Paramètres**:
- `delta_str`: Format `[+/-]YYYYMMDD_HHMMSS`

**Retourne**:
- Tuple `(total_days, total_seconds)`

**Exemple**:
```python
days, seconds = parse_time_delta("+00000001_020000")
# days = 1, seconds = 7200 (2 heures)
```

### `apply_time_delta(dt, delta_str) -> datetime`

Applique un delta à un datetime.

**Paramètres**:
- `dt`: Datetime original
- `delta_str`: Delta au format standard

**Retourne**:
- Nouveau datetime ajusté

**Exemple**:
```python
original = datetime(2024, 10, 15, 23, 0, 0)
adjusted = apply_time_delta(original, "+00000000_020000")
# adjusted = datetime(2024, 10, 16, 1, 0, 0)  ← Rollover!
```

### `load_group_time_adjustments(config_path) -> dict`

Charge les ajustements depuis le JSON.

**Paramètres**:
- `config_path`: Chemin du fichier JSON (optionnel, détecté automatiquement)

**Retourne**:
- Dictionnaire `{groupe: delta}` (clés en minuscules)

**Exemple**:
```python
adjustments = load_group_time_adjustments()
# {"canon": "+00000001_000000", "gopro": "-00000000_020000"}
```

### `adjust_datetime_for_group(dt, group_name, adjustments) -> datetime`

Applique l'ajustement si configuré pour le groupe.

**Paramètres**:
- `dt`: Datetime original
- `group_name`: Nom du groupe (case-insensitive)
- `adjustments`: Dictionnaire chargé par `load_group_time_adjustments`

**Retourne**:
- Datetime ajusté (ou original si pas d'ajustement)

**Exemple**:
```python
dt = datetime(2024, 10, 15, 14, 0, 0)
adjustments = {"canon": "+00000001_000000"}
adjusted = adjust_datetime_for_group(dt, "canon", adjustments)
# adjusted = datetime(2024, 10, 16, 14, 0, 0)
```

## 📝 Modifications du Code

### `file_date()` - Signature Modifiée

**Avant**:
```python
def file_date(p: Path, tz_name: str = "America/Montreal"):
    # ...
    return dt.date()
```

**Après**:
```python
def file_date(p: Path, tz_name: str = "America/Montreal", 
              group_name: str = None, time_adjustments: dict = None):
    
    # Helper function to apply adjustments
    def apply_adjustment_and_return(dt_obj):
        if time_adjustments and group_name:
            adjusted_dt = adjust_datetime_for_group(dt_obj, group_name, time_adjustments)
            return adjusted_dt.date()
        return dt_obj.date()
    
    # Extract datetime
    dt = extract_datetime(p)
    
    # Apply adjustment before returning
    return apply_adjustment_and_return(dt)
```

### Boucle Principale

**Avant**:
```python
for idx, (f, file_type) in enumerate(all_files, start=1):
    d = file_date(f, args.tz)
    src = source_name(f, input_root)
```

**Après**:
```python
# Load adjustments once at startup
time_adjustments = load_group_time_adjustments()

for idx, (f, file_type) in enumerate(all_files, start=1):
    src = source_name(f, input_root)  # Get group first
    d = file_date(f, args.tz, src, time_adjustments)  # Pass group & adjustments
```

## ⚠️  Considérations Importantes

### 1. Case-Insensitive

Les noms de groupes sont **insensibles à la casse**:
```json
{"Canon": "+00000001_000000"}
```
Matche aussi: `canon`, `CANON`, `CaNoN`

### 2. Approximations

- **Mois** = 30 jours (fixe)
- **Années** = 365 jours (pas de gestion des années bissextiles)

Pour des ajustements précis au mois, utiliser plutôt les jours:
```json
{"groupe": "+00000030_000000"}  // 30 jours au lieu de "+00000100_000000"
```

### 3. Ordre d'Application

Les ajustements sont appliqués **après** l'extraction de la date originale mais **avant** la création des dossiers de destination.

Flux:
1. Extraction date/heure depuis métadonnées
2. ✨ **Application ajustement** ✨
3. Création du dossier `YYYY-MM-DD/`
4. Création du placeholder JSON

### 4. Fichiers Sans Métadonnées

Si un fichier n'a **pas de métadonnées temporelles valides**:
- Il est placé dans `date_non_valide/`
- **Aucun ajustement n'est appliqué** (pas de date de base)

## 🎉 Avantages

### ✅ Flexibilité

Ajuster n'importe quel groupe indépendamment sans modifier les fichiers sources.

### ✅ Précision

Gestion correcte des rollovers temporels (heures → jours → mois → années).

### ✅ Réversibilité

Les fichiers originaux ne sont jamais modifiés. On peut:
1. Supprimer `Footage_metadata_sorted/`
2. Modifier la configuration
3. Re-exécuter le script

### ✅ Traçabilité

Chaque ajustement est loggé:
```
INFO: ⏰ Applied time adjustment to group 'canon': +00000001_000000
DEBUG:    Original: 2024-10-14 14:30:00
DEBUG:    Adjusted: 2024-10-15 14:30:00
```

### ✅ Maintenabilité

Configuration JSON simple et lisible, pas de code à modifier.

## 📚 Exemples de Configurations

### Cas 1: Appareil en Retard d'un Jour
```json
{
    "canon": "+00000001_000000"
}
```

### Cas 2: Appareil en Avance de 2 Heures
```json
{
    "gopro": "-00000000_020000"
}
```

### Cas 3: Correction de Fuseau Horaire (+5h)
```json
{
    "cellphone": "+00000000_050000"
}
```

### Cas 4: Plusieurs Groupes
```json
{
    "canon": "+00000001_000000",
    "gopro": "-00000000_020000",
    "dji_drone": "+00000000_003000"
}
```

### Cas 5: Ajustement Complexe
```json
{
    "old_camera": "+00010203_123045"
}
```
- +1 an, +2 mois (60 jours), +3 jours
- +12h, +30min, +45sec
- Total: ~428 jours + 12h30:45

## 🔄 Workflow Complet

### Étape 1: Identifier le Problème

Constater que les fichiers d'un groupe ont des dates incorrectes.

**Exemple**: Les fichiers du groupe `canon` sont tous datés d'un jour en retard.

### Étape 2: Créer la Configuration

Créer `specific_group_time_adjust.json`:
```json
{
    "canon": "+00000001_000000"
}
```

### Étape 3: Exécuter le Script

```bash
python SORTING/organize_footage_links.py project_folder
```

### Étape 4: Vérifier les Logs

```
INFO: ⏰ Loaded time adjustments for 1 group(s) from specific_group_time_adjust.json
...
INFO: ⏰ Applied time adjustment to group 'canon': +00000001_000000
```

### Étape 5: Valider le Résultat

Vérifier que les fichiers sont dans les bons dossiers de dates.

### Étape 6: (Optionnel) Ajuster et Re-exécuter

Si l'ajustement n'est pas correct:
1. Supprimer `Footage_metadata_sorted/`
2. Modifier `specific_group_time_adjust.json`
3. Re-exécuter le script

## 🎯 Conclusion

Cette fonctionnalité permet de **corriger facilement les décalages temporels** causés par des erreurs de configuration d'appareils, sans jamais modifier les fichiers originaux, avec une **gestion correcte des rollovers temporels** (heures → jours → années).

**Résultat**: Organisation parfaite même avec des appareils mal configurés! 🚀
