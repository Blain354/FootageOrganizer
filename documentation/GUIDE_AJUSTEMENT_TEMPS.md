# 🕐 Ajustement Temporel par Groupe - Guide Rapide

## 📌 Vue d'ensemble

Cette fonctionnalité permet d'ajuster automatiquement la date/heure d'acquisition des fichiers en fonction de leur groupe source, idéal pour corriger les erreurs d'horloge des appareils.

## 🚀 Démarrage Rapide

### 1. Créer le fichier de configuration

Créer `specific_group_time_adjust.json` à la racine du projet:

```json
{
    "canon": "+00000001_000000"
}
```

Ce fichier indique: "Pour tous les fichiers du groupe **canon**, ajouter **1 jour**"

### 2. Exécuter le script

```bash
python SORTING/organize_footage_links.py project_folder
```

### 3. Vérifier les résultats

Les fichiers du groupe `canon` seront organisés avec une date ajustée de +1 jour.

## 📝 Format du Delta

Format: `[+/-]YYYYMMDD_HHMMSS`

### Exemples Courants

| Configuration | Signification |
|--------------|---------------|
| `"+00000001_000000"` | Ajouter 1 jour |
| `"-00000001_000000"` | Soustraire 1 jour |
| `"+00000000_020000"` | Ajouter 2 heures |
| `"-00000000_010000"` | Soustraire 1 heure |
| `"+00000007_000000"` | Ajouter 7 jours (1 semaine) |

### Décomposition du Format

Pour `+00000001_020030`:
- `+` : Ajouter (ou `-` pour soustraire)
- `0000` : Années
- `00` : Mois (approximé à 30 jours chacun)
- `01` : Jours
- `_` : Séparateur
- `02` : Heures
- `00` : Minutes  
- `30` : Secondes

**Résultat**: Ajoute 1 jour + 2 heures + 30 secondes

## 🎯 Cas d'Usage

### Cas 1: Appareil avec horloge en retard

**Problème**: Votre Canon affiche toujours un jour de retard.

**Solution**:
```json
{
    "canon": "+00000001_000000"
}
```

### Cas 2: Décalage horaire non corrigé

**Problème**: Votre GoPro est encore réglée sur votre fuseau horaire précédent (+5h).

**Solution**:
```json
{
    "gopro": "-00000000_050000"
}
```

### Cas 3: Plusieurs appareils à corriger

**Solution**:
```json
{
    "canon": "+00000001_000000",
    "gopro": "-00000000_050000",
    "old_camera": "+00000003_000000"
}
```

## 🔍 Vérification

### Avant l'ajustement

```
Footage_raw/
  canon/
    IMG_1234.MOV  → métadonnées: 2024-10-14 14:30:00
```

### Après l'ajustement

```
Footage_metadata_sorted/
  video/
    2024-10-15/  ← Date ajustée (+1 jour)
      14h30m00s_canon_IMG_1234.json
```

## 📊 Tests

### Script de Test Basique

```bash
python test_time_adjustment.py
```

Valide les fonctions de parsing et d'application des deltas.

### Script de Démonstration

```bash
python demo_time_adjustment.py
```

Simule le traitement de fichiers avec différents groupes et affiche les résultats.

## ⚠️  Points Importants

### 1. Rollover Temporel Automatique

Si un fichier est à **23h00** et que vous ajoutez **2 heures**, il passe automatiquement au **jour suivant à 1h00**.

**Exemple**:
```
Original:  2024-10-15 23:00:00
Delta:     +00000000_020000 (add 2 hours)
Adjusted:  2024-10-16 01:00:00  ← Jour suivant!
```

### 2. Noms de Groupes Case-Insensitive

```json
{"Canon": "+00000001_000000"}
```

Matche: `canon`, `CANON`, `CaNoN`, etc.

### 3. Fichiers Sans Métadonnées

Les fichiers sans date valide vont dans `date_non_valide/` et **ne sont pas ajustés**.

### 4. Approximations

- **1 mois** = 30 jours (fixe)
- **1 an** = 365 jours (pas d'années bissextiles)

Pour plus de précision, utilisez directement les jours:
```json
{"groupe": "+00000030_000000"}  // 30 jours au lieu de "+00000100_000000" (1 mois)
```

## 📖 Logs

Quand un ajustement est appliqué, vous verrez:

```
INFO: ⏰ Loaded time adjustments for 1 group(s) from specific_group_time_adjust.json
...
INFO: ⏰ Applied time adjustment to group 'canon': +00000001_000000
DEBUG:    Original: 2024-10-14 14:30:00
DEBUG:    Adjusted: 2024-10-15 14:30:00
INFO: 📅 Using metadata date for IMG_1234.MOV: 2024-10-15
```

## 🔄 Workflow Complet

1. **Identifier** le groupe problématique et le décalage
2. **Créer/Modifier** `specific_group_time_adjust.json`
3. **Exécuter** le script d'organisation
4. **Vérifier** les logs et les dossiers de destination
5. **(Si nécessaire)** Supprimer la sortie, ajuster la config, et ré-exécuter

## 📚 Documentation Complète

Pour plus de détails, consultez: `AJUSTEMENT_TEMPOREL_GROUPES.md`

## 🎉 Avantages

✅ **Non-destructif** - Les fichiers originaux ne sont jamais modifiés  
✅ **Flexible** - Un ajustement différent par groupe  
✅ **Précis** - Gestion correcte des rollovers temporels  
✅ **Simple** - Configuration JSON lisible  
✅ **Réversible** - On peut toujours ré-exécuter avec une nouvelle config

## 🆘 Aide

**Problème**: Les fichiers ne vont pas dans les bons dossiers.

**Solution**: Vérifiez le format du delta et testez avec `demo_time_adjustment.py` avant.

**Problème**: Le groupe n'est pas reconnu.

**Solution**: Assurez-vous que le nom dans le JSON correspond au nom du dossier sous `Footage_raw/`.

---

**Questions?** Consultez la documentation complète: `AJUSTEMENT_TEMPOREL_GROUPES.md`
