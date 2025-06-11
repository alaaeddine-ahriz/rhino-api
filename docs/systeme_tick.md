# Planification des défis par système de Tick

Ce document explique **comment les défis (challenges) sont distribués dans le temps** à l'aide du mécanisme de *tick* implémenté dans le backend.

---

## 1. Concepts clés

| Terme | Signification |
|-------|---------------|
| **Matière** | Une UE / un cours (ex. `SYD`, `TCP`). |
| **Granularité** | Fréquence à laquelle un nouveau défi pour une matière devient disponible. Exemples : `jour`, `semaine`, `3jours`, `mois`. Valeur stockée dans `matiere.granularite`. |
| **Tick** | Compteur entier qui s'incrémente selon la granularité. Tous les utilisateurs voient **le même défi** pour une matière donnée pendant un tick donné. |
| **ChallengeServed** | Table qui mémorise quel défi (via `ref`) a été servi pour chaque couple `(matiere, granularite, tick)`. Empêche la répétition tant que tous les défis n'ont pas été vus. |

---

## 2. Calcul du Tick

Le système utilise **une date de référence globale** (paramètre `TICK_REFERENCE_DATE` dans `app/core/config.py`, par défaut `2024-01-01`).

La fonction `compute_tick(granularite, ref_date_str)` (dans `app/services/challenges.py`) convertit **« aujourd'hui »** en un numéro de tick ; on lui passe maintenant cette date de référence globale.

1. **Parsing** : `ref_date_str` est analysée par `_parse_date()` qui reconnaît actuellement :
   * `YYYY-MM-DD` (ISO)
   * `DD/MM/YYYY`
   * `DD/MM/YY`
   * `YYYY/MM/DD`

2. **Calcul du delta**

```python
now        = datetime.now()
ref_date   = date de référence  # souvent la date du *premier* challenge
elapsed    = (now.date() – ref_date.date()).days
```

3. **Conversion selon la granularité**

| Granularité | Formule Tick |
|-------------|--------------|
| `jour`      | `elapsed` |
| `semaine`   | `elapsed // 7` |
| `mois`      | `(now.year - ref.year) * 12 + (now.month - ref.month)` |
| `Njours` (`3jours`…) | `elapsed // N` |

Toute autre valeur lève `ValueError("Granularité non supportée")`.

Comme le tick dépend uniquement des dates, **tous les serveurs** et **tous les utilisateurs** obtiennent la même valeur de tick pour une matière à une date donnée (hors décalage de fuseau horaire).

---

## 3. Sélection du défi pour un Tick

Fonction : `get_challenge_for_current_tick(matiere, session, granularite=None)`

1. Récupère la granularité de la matière ou la valeur par défaut.
2. Charge tous les défis de la matière (triés) et génère une `ref` (`<MAT>-<ID sur 3 chiffres>`).
3. Calcule `current_tick`.
4. Cherche dans `ChallengeServed` une ligne correspondant à `(matiere, granularite, current_tick)` :
   * **Trouvée** → retourne le défi déjà servi.
5. Sinon :
   * récupère toutes les `challenge_ref` déjà servies pour ce couple.
   * choisit le premier défi jamais servi ; si tous ont déjà été vus, **réinitialise** (supprime les lignes) et recommence.
6. Insère une nouvelle ligne `ChallengeServed` avec `(matiere, granularite, chosen_ref, tick)`.
7. Retourne le défi.

> ⚙️  Garantit **exactement un défi** par matière et par tick, et un cycle complet sur tous les défis disponibles.

### Où est stocké le **tick courant** ?

*Le tick n'est **pas** enregistré en permanence dans la base.*

1. À chaque appel, le backend **recalcule** `current_tick` à partir de la date du jour et de la granularité (voir §2).  
2. La table `challengeserved` conserve l'historique : pour chaque tick déjà servi on y trouve `(matiere, granularite, challenge_ref, tick)`.  
3. L'état actuel est donc **dérivé** du calcul + de la présence (ou non) d'une entrée pour ce tick.

Cette approche évite d'avoir un compteur global à maintenir ; la logique est purement fonctionnelle et idempotente.

### Algorithme de choix détaillé

1. **Rechercher un défi déjà servi** pour `(matiere, granularite, current_tick)` :  
   – S'il existe ⇒ on renvoie ce même défi (garantie d'idempotence).  
   – Sinon ⇒ on doit en sélectionner un nouveau.
2. **Lister les références déjà servies** (toutes lignes `challengeserved` de la matière + granularité).
3. **Parcourir les défis de la matière** dans l'ordre chronologique :
   * le premier dont la `ref` n'est **pas** dans la liste devient `selected_challenge` ;
   * s'il n'en reste aucun, on considère que le cycle est terminé :  
     a. on **supprime** toutes les lignes `challengeserved` de cette matière + granularité (reset),  
     b. on reprend au tout premier défi de la liste.
4. **Persist** une nouvelle ligne `challengeserved` avec le tick courant :`(matiere, granularite, selected_ref, current_tick)`.
5. Retourner le défi.

Ainsi :
* le même défi n'est jamais servi deux fois pendant un même tick ;
* l'ensemble des défis est parcouru avant de boucler ;
* l'ajout/suppression d'un défi dans la liste ne casse pas le système ; il sera simplement pris en compte lors du cycle suivant.

---

## 4. Round-Robin pour abonnements multiples

`get_today_challenge_for_user(subscriptions, session)`

1. Sépare les matières de l'utilisateur.
2. Pour chaque matière : appel à `get_challenge_for_current_tick()` ; on garde celles qui ont un défi **aujourd'hui**.
3. Aucune disponible ? → pas de défi aujourd'hui.
4. **Sélection ronde : round-robin**

```python
idx = date.today().toordinal() % len(eligible_subjects)
selected = eligible_subjects[idx]
```

Ainsi l'utilisateur reçoit *un* seul défi par jour et on alterne équitablement entre ses matières, quelle que soit leur granularité.

---

## 5. Extensions possibles

* **Heure de réinitialisation** : utiliser un objet timezone-aware ou arrondir à minuit UTC.
* **Streaks / difficulté** : stocker des métadonnées par utilisateur et ajuster la logique.
* **Plusieurs défis par jour** : renvoyer la liste complète des défis éligibles au lieu d'un seul.

---

## 6. Schéma minimal des tables SQL

```text
matiere(id, name, granularite, …)
challenge(id, question, matiere, date, …)
challengeserved(id, matiere, granularite, challenge_ref, tick)
```

Ces trois tables pilotent le mécanisme de planification par tick. 