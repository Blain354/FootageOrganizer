# ⏰ Nouvelle Fonctionnalité: Ajustement Temporel par Groupe

## 🎉 Disponible Maintenant!

Vous pouvez maintenant **corriger automatiquement** les erreurs d'horloge de vos appareils photo/vidéo!

## 🚀 Utilisation en 3 Étapes

### Étape 1: Créer le Fichier de Configuration

Créez un fichier nommé **`specific_group_time_adjust.json`** à la racine de votre projet:

```json
{
    "canon": "+00000001_000000"
}
```

Ce fichier signifie: "Ajouter 1 jour à tous les fichiers du groupe **canon**"

### Étape 2: Exécuter le Script Normalement

```bash
python SORTING/organize_footage_links.py votre_projet
```

### Étape 3: C'est Tout! ✨

Les fichiers du groupe `canon` seront automatiquement organisés avec +1 jour ajouté à leur date.

## 📝 Format Simple

`[+/-]YYYYMMDD_HHMMSS`

### Exemples Rapides

| Ce que vous voulez | Configuration |
|-------------------|---------------|
| Ajouter 1 jour | `"+00000001_000000"` |
| Soustraire 1 jour | `"-00000001_000000"` |
| Ajouter 2 heures | `"+00000000_020000"` |
| Soustraire 3 heures | `"-00000000_030000"` |
| Ajouter 1 semaine | `"+00000007_000000"` |

## 💡 Exemple Concret

### Problème
Votre Canon affiche toujours un jour de retard. Vos vidéos du 14 octobre devraient être datées du 15 octobre.

### Solution

**Créer `specific_group_time_adjust.json`:**
```json
{
    "canon": "+00000001_000000"
}
```

**Exécuter:**
```bash
python SORTING/organize_footage_links.py mon_projet
```

**Résultat:**
```
Avant:  video/2024-10-14/14h30m00s_canon_IMG_1234.json
Après:  video/2024-10-15/14h30m00s_canon_IMG_1234.json
        ^^^^^^^^^^^^
        Date corrigée!
```

## ✨ Fonctionnalités

✅ **Rollover Automatique**: 23h + 2h = 01h le jour suivant  
✅ **Multiple Groupes**: Configurez plusieurs caméras  
✅ **Safe**: Fichiers originaux jamais modifiés  
✅ **Simple**: Configuration JSON facile  
✅ **Précis**: Gestion correcte des heures, jours, mois, années

## 📖 Documentation Complète

- **Guide rapide**: `GUIDE_AJUSTEMENT_TEMPS.md`
- **Documentation technique**: `AJUSTEMENT_TEMPOREL_GROUPES.md`
- **Tests**: `python test_time_adjustment.py`
- **Démo**: `python demo_time_adjustment.py`

## 🎬 Démo Rapide

Testez avant d'utiliser:

```bash
python demo_time_adjustment.py
```

Voir le résultat sans toucher vos fichiers!

## 🆘 Besoin d'Aide?

### Trouver le Nom du Groupe

Le nom du groupe = le nom du dossier sous `Footage_raw/`:

```
Footage_raw/
  canon/        ← Nom du groupe: "canon"
  gopro/        ← Nom du groupe: "gopro"
  dji_drone/    ← Nom du groupe: "dji_drone"
```

### Plusieurs Corrections

```json
{
    "canon": "+00000001_000000",
    "gopro": "-00000000_020000",
    "old_camera": "+00000003_000000"
}
```

### Questions Fréquentes

**Q: Est-ce que ça modifie mes fichiers originaux?**  
R: Non, jamais! Seule l'organisation change.

**Q: Je peux annuler?**  
R: Oui! Supprimez `Footage_metadata_sorted/`, modifiez la config, et ré-exécutez.

**Q: Ça marche avec les photos?**  
R: Oui, pour tout fichier avec des métadonnées valides.

**Q: Et si je me trompe dans la configuration?**  
R: Testez d'abord avec `demo_time_adjustment.py`!

## 🎊 C'est Tout!

Simple, efficace, et sûr. Profitez de l'organisation parfaite même avec des appareils mal configurés! 🚀

---

**Date d'ajout:** 28 octobre 2025  
**Version:** 1.0  
**Statut:** ✅ Production Ready
