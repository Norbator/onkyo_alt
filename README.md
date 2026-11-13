# Onkyo Alt

Distribution alternative de l'intégration Onkyo de Home Assistant, adossée à
[`aioonkyo_alt`](https://github.com/Norbator/aioonkyo_alt), fork de
[`aioonkyo`](https://github.com/arturpragacz/aioonkyo) par Artur Pragacz.

**Ce n'est pas une amélioration de l'intégration officielle.** C'est la même
intégration, avec quelques réglages ISCP supplémentaires qui n'ont pas encore
été proposés en amont. Si vous n'avez pas besoin de ces réglages, utilisez
l'intégration Onkyo officielle : elle est maintenue, celle-ci ne l'est que par
son auteur.

Le suffixe `_alt` sert à éviter toute collision de domaine et de paquet
Python, rien de plus.

## Réglages ajoutés

| Entité | ISCP | Plage | Testé sur |
|---|---|---|---|
| `number` Dialog enhancement | `VOC` | 0–5 | Pioneer VSX-LX305 |

## Installation

HACS → menu ⋮ → *Dépôts personnalisés* → URL de ce dépôt, catégorie
*Integration*. Installer **Onkyo Alt**, puis redémarrer Home Assistant.

Home Assistant installe `aioonkyo_alt` depuis PyPI automatiquement : aucune
image conteneur dérivée n'est nécessaire.

> **Retirez d'abord l'entrée de configuration Onkyo officielle.** Les deux
> intégrations ouvriraient chacune une connexion eISCP vers le même ampli,
> ce qui fait décrocher la connexion.

## Compatibilité

Home Assistant **2026.11 et suivantes**. Le code suit l'intégration Onkyo du
cœur en version 2026.11.1, y compris `async_setup_entry` / `async_unload_entry`
qui ne renvoient plus rien et `async_unload_platforms_or_raise`, absents de
2026.10. Pour Home Assistant 2026.10, utiliser onkyo_alt **0.1.2**.

Les tests du cœur, adaptés à onkyo_alt :

```bash
uv venv -p 3.14
uv pip install homeassistant==2026.11.1 pytest-homeassistant==2026.11.1 aioonkyo_alt==0.4.0.post2
uv run --no-project python -m pytest -q
```

## Ajouter un réglage

1. Sniffer le code réel sur votre ampli — ne jamais se fier à une table de
   commandes trouvée en ligne sans l'avoir vérifiée sur le matériel.
2. Ajouter le code dans `aioonkyo_alt` (5 points d'insertion).
3. Ajouter une entrée dans `NUMBERS` (`custom_components/onkyo_alt/number.py`)
   et la clé de traduction correspondante.

## Remerciements

À Artur Pragacz pour `aioonkyo` et pour l'intégration Onkyo du cœur de
Home Assistant, dont tout ce dépôt dérive.

## Licence

GPL-3.0-only. Voir `NOTICE`.
