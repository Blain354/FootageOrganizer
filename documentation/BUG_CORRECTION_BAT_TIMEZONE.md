# 🐛 Correction Bug: Timezone non passée dans le .BAT

## 📅 Date: 28 octobre 2025

## ❌ Problème Signalé

> "Quand je change la timezone dans le fichier .bat, il n'y a rien qui se passe de différent"

L'utilisateur modifiait la variable `TIMEZONE` dans le fichier `SORT_MEDIA_FOLDER.BAT` mais cela n'avait aucun effet sur l'organisation des fichiers.

## 🔍 Cause du Bug

Le fichier `.bat` définissait bien la variable `TIMEZONE`:

```bat
set TIMEZONE=America/Montreal
```

**MAIS** elle n'était **jamais utilisée** lors de l'appel à `organize_footage_links.py`!

### Code Bugué

```bat
python organize_footage_links.py "%TARGET_PATH%" --include-photos
```

↑ La variable `%TIMEZONE%` n'était pas passée en paramètre!

### Conséquence

Le script Python utilisait toujours la **timezone par défaut** définie dans son code (`America/Montreal`), peu importe ce que l'utilisateur changeait dans le fichier `.bat`.

## ✅ Correction

### Code Corrigé

```bat
python organize_footage_links.py "%TARGET_PATH%" --include-photos --tz "%TIMEZONE%"
```

↑ Ajout du paramètre `--tz "%TIMEZONE%"` pour transmettre la timezone au script Python.

### Impact

✅ **Maintenant fonctionnel**: Changer `TIMEZONE` dans le `.bat` affecte correctement l'organisation  
✅ **Rétrocompatible**: Si la variable n'est pas définie, Python utilise sa valeur par défaut  
✅ **Documenté**: Le commentaire en haut du `.bat` explique comment modifier la timezone

## 📝 Fichier Modifié

**Fichier**: `SORTING/SORT_MEDIA_FOLDER.BAT`

**Ligne modifiée**: ~180

```diff
- python organize_footage_links.py "%TARGET_PATH%" --include-photos
+ python organize_footage_links.py "%TARGET_PATH%" --include-photos --tz "%TIMEZONE%"
```

## 🎯 Utilisation Corrigée

### Modifier la Timezone

**Éditer le fichier** `SORT_MEDIA_FOLDER.BAT`:

```bat
REM Ligne 34: Changer la timezone
set TIMEZONE=Europe/Paris
```

**Timezones courantes**:
- `America/Montreal` (UTC-5 hiver, UTC-4 été)
- `America/New_York` (UTC-5 hiver, UTC-4 été)
- `Europe/Paris` (UTC+1 hiver, UTC+2 été)
- `Asia/Tokyo` (UTC+9)
- `Australia/Sydney` (UTC+10 été, UTC+11 hiver)
- `UTC` (pas de décalage)

### Exécuter le Script

```bat
SORT_MEDIA_FOLDER.BAT "C:\path\to\projet"
```

Le script utilisera maintenant la timezone spécifiée!

## 🧪 Test de Validation

### Configuration

```bat
REM Test 1: Montreal
set TIMEZONE=America/Montreal

REM Test 2: Paris
set TIMEZONE=Europe/Paris

REM Test 3: Tokyo
set TIMEZONE=Asia/Tokyo
```

### Résultat Attendu

Avec une vidéo drone ayant `creation_time = 2024-10-15T18:30:00Z` (UTC):

| TIMEZONE | Heure Locale | Nom Fichier |
|----------|--------------|-------------|
| `America/Montreal` (UTC-4) | 14:30 | `14h30m00s_dji_*.json` |
| `Europe/Paris` (UTC+2) | 20:30 | `20h30m00s_dji_*.json` |
| `Asia/Tokyo` (UTC+9) | 03:30 (lendemain) | `03h30m00s_dji_*.json` |

**Avant la correction**: Toujours `14h30m00s` (valeur par défaut)  
**Après la correction**: Heure correcte selon timezone ✅

## 🔗 Bugs Liés

Ce bug était **masqué** par le **[BUG_CORRECTION_UTC.md](BUG_CORRECTION_UTC.md)** qui lui aussi empêchait les conversions timezone de fonctionner correctement.

**Chronologie des bugs**:
1. **Bug UTC** (corrigé) - Les conversions timezone étaient cassées dans le code Python
2. **Bug BAT** (corrigé maintenant) - La timezone n'était pas passée au script Python

Les deux devaient être corrigés pour que la fonctionnalité timezone fonctionne complètement.

## 📚 Documentation Liée

- **[BUG_CORRECTION_UTC.md](BUG_CORRECTION_UTC.md)** - Bug conversion UTC (corrigé avant)
- **[TIMEZONE_UTILISATION.md](TIMEZONE_UTILISATION.md)** - Guide utilisation timezone
- **README.md** - Documentation utilisateur

## 🎉 Statut

✅ **Bug corrigé**  
✅ **Paramètre `--tz` maintenant transmis correctement**  
⏳ **Tests utilisateur**: À valider avec différentes timezones

---

**Date**: 28 octobre 2025  
**Impact**: Majeur - empêchait toute utilisation de la timezone via le .bat  
**Correction**: 1 ligne changée dans `SORT_MEDIA_FOLDER.BAT`
