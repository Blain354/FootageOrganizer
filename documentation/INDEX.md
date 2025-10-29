# 📚 Documentation - Footage Organization System

## 📑 Index des Documents

### 🆕 Fonctionnalités Principales

#### Ajustement Temporel par Groupe
- **[GUIDE_AJUSTEMENT_TEMPS.md](GUIDE_AJUSTEMENT_TEMPS.md)** - Guide utilisateur rapide ⭐
  - Configuration JSON
  - Exemples d'utilisation
  - Cas d'usage courants
  
- **[AJUSTEMENT_TEMPOREL_GROUPES.md](AJUSTEMENT_TEMPOREL_GROUPES.md)** - Documentation technique complète
  - Architecture et fonctionnement
  - API des fonctions
  - Tests et validation

- **[NOUVELLE_FONCTIONNALITE.md](NOUVELLE_FONCTIONNALITE.md)** - Annonce de la fonctionnalité
  - Vue d'ensemble rapide
  - Exemples concrets

#### Visualisation de Métadonnées
- **[GUIDE_METADATA_VIEWER.md](GUIDE_METADATA_VIEWER.md)** - Guide du visualiseur de métadonnées
  - Utilisation de `show_file_metadata.py`
  - Débogage des fichiers

- **[NOUVEAU_OUTIL_METADATA.md](NOUVEAU_OUTIL_METADATA.md)** - Présentation de l'outil
  - Fonctionnalités du visualiseur

#### Configuration Timezone
- **[TIMEZONE_UTILISATION.md](TIMEZONE_UTILISATION.md)** - Quand et comment utiliser la timezone ⭐
  - Portée de la timezone (vidéos drone uniquement)
  - Pourquoi ça ne fonctionne pas pour les photos
  - Alternative: ajustement temporel

### 🔄 Changelogs et Historique

- **[CHANGEMENT_FORMAT_JSON.md](CHANGEMENT_FORMAT_JSON.md)** - Migration TXT → JSON
  - Nouveau format des placeholders
  - Métadonnées raw incluses
  
- **[CHANGELOG_STRUCTURE.md](CHANGELOG_STRUCTURE.md)** - Changement de structure
  - Organisation photo/ et video/
  - Nouvelle arborescence

- **[AMELIORATION_LOGGING.md](AMELIORATION_LOGGING.md)** - Système de logging coloré
  - Couleurs ANSI
  - Amélioration de l'affichage console

### 📋 Résumés Techniques

- **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - État d'implémentation
  - Checklist complète
  - Résultats de tests
  - Statut production

- **[FICHIERS_CREES_MODIFIES.md](FICHIERS_CREES_MODIFIES.md)** - Liste des modifications
  - Fichiers créés/modifiés
  - Statistiques de code
  - Structure finale

## 🎯 Navigation Rapide

### Pour Démarrer
1. Lire le [README.md](../README.md) principal à la racine
2. Consulter [GUIDE_AJUSTEMENT_TEMPS.md](GUIDE_AJUSTEMENT_TEMPS.md) pour l'ajustement temporel

### Pour Comprendre les Changements
1. [CHANGELOG_STRUCTURE.md](CHANGELOG_STRUCTURE.md) - Nouvelle structure photo/video
2. [CHANGEMENT_FORMAT_JSON.md](CHANGEMENT_FORMAT_JSON.md) - Migration vers JSON
3. [AMELIORATION_LOGGING.md](AMELIORATION_LOGGING.md) - Logs colorés

### Pour Déboguer
1. [GUIDE_METADATA_VIEWER.md](GUIDE_METADATA_VIEWER.md) - Visualiser métadonnées
2. [NOUVEAU_OUTIL_METADATA.md](NOUVEAU_OUTIL_METADATA.md) - Outil de débogage

### Pour les Développeurs
1. [AJUSTEMENT_TEMPOREL_GROUPES.md](AJUSTEMENT_TEMPOREL_GROUPES.md) - Architecture technique
2. [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - État du code
3. [FICHIERS_CREES_MODIFIES.md](FICHIERS_CREES_MODIFIES.md) - Modifications détaillées

## 📊 Organisation

```
documentation/
├── INDEX.md                              [Ce fichier]
│
├── Guides Utilisateur/
│   ├── GUIDE_AJUSTEMENT_TEMPS.md        ⭐ Guide ajustement temporel
│   └── GUIDE_METADATA_VIEWER.md          Visualiseur métadonnées
│
├── Documentation Technique/
│   ├── AJUSTEMENT_TEMPOREL_GROUPES.md    Architecture ajustement
│   └── NOUVEAU_OUTIL_METADATA.md         Outil métadonnées
│
├── Changelogs/
│   ├── CHANGEMENT_FORMAT_JSON.md         Migration JSON
│   ├── CHANGELOG_STRUCTURE.md            Nouvelle structure
│   ├── AMELIORATION_LOGGING.md           Logs colorés
│   └── DRONE_PHOTOS_MTIME.md             Photos drone avec mtime ⭐
│
├── Résumés/
│   ├── NOUVELLE_FONCTIONNALITE.md        Annonce ajustement
│   ├── IMPLEMENTATION_COMPLETE.md        État implémentation
│   ├── FICHIERS_CREES_MODIFIES.md        Liste modifications
│   ├── REORGANISATION.md                 Réorganisation détaillée
│   └── REORGANISATION_COMPLETE.md        Résumé réorganisation ⭐
│
└── debug/
    └── README.md                          Debug tools
```

## 🔗 Liens Externes

- **Projet GitHub**: FootageOrganizer (Blain354)
- **README Principal**: [../README.md](../README.md)
- **Scripts**: [../SORTING/](../SORTING/)
- **Debug Tools**: [../debug/](../debug/)

## 📝 Notes

- ⭐ = Documentation essentielle pour les utilisateurs
- Documents techniques pour développeurs et maintenance
- Changelogs pour historique des modifications
- Tous les tests unitaires ont été supprimés après validation

---

**Dernière mise à jour**: 28 octobre 2025  
**Version**: 1.0 (Production Ready)
