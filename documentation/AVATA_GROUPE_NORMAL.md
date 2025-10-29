# 🎮 Avata: Groupe Normal (Non-Drone)

## 📅 Date: 28 octobre 2025

## 🎯 Changement

**Avata est maintenant traité comme un groupe NORMAL**, pas comme un drone.

## 📊 Comportement

### Avant
- Avata détecté comme drone
- Traitement spécial avec mtime

### Après
- Avata = groupe normal (comme Canon, iPhone, etc.)
- Extraction date via méthodes standards:
  1. Filename pattern (si présent)
  2. Exiftool (métadonnées)
  3. mtime (fallback)
- Ajustement temporel appliqué si configuré

## 🔧 Configuration

### Dossier
```
Footage_raw/
  avata/              ← Groupe normal "avata"
    video001.mp4
    photo001.jpg
```

### Ajustement Temporel
```json
{
    "avata": "+00000000_040000"
}
```
↑ Fonctionne normalement comme pour tout groupe

## 🔍 Détection Drone Modifiée

### Code
```python
def _path_has_drone_segment(p: Path) -> bool:
    """Vérifie si le chemin contient un dossier commençant par 'drone' ou 'dji'"""
    return any(part.lower().startswith(("drone", "dji", "mini4")) for part in p.parts)
```

**Détecte**: `drone`, `dji`, `mini4`  
**Ne détecte PLUS**: `avata` ❌

## 📋 Drones Restants

| Dossier | Détecté Comme Drone? | Conversion UTC? |
|---------|---------------------|-----------------|
| `drone/` | ✅ Oui | ✅ Oui (vidéos) |
| `dji/` | ✅ Oui | ✅ Oui (vidéos) |
| `mini4/` | ✅ Oui | ✅ Oui (vidéos) |
| `avata/` | ❌ **Non** | ❌ **Non** |

## 🎯 Résultat

**Avata** fonctionne maintenant comme:
- Canon
- iPhone
- GoPro
- N'importe quel autre groupe

**Extraction date**:
1. Pattern filename → utilise filename
2. Métadonnées exiftool → utilise métadonnées
3. Fallback → utilise mtime
4. Ajustement temporel appliqué

**Pas de conversion UTC** (comme demandé)

---

**Date**: 28 octobre 2025  
**Changement**: Avata retiré de la liste des drones  
**Status**: ✅ Implémenté
