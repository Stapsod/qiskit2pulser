# qiskit2pulser

Projet perso d'apprentissage : un compilateur qui prend un `QuantumCircuit` Qiskit et produit une `Sequence` Pulser (atomes neutres). D'abord le mode digital (portes → impulsions), le mode analogique viendra plus tard.

## Comment travailler avec l'utilisateur

- On échange en français, mais les commentaires et docstrings du code sont en anglais.
- Mode mentorat : j'explique les concepts et fixe l'objectif de chaque étape. **L'utilisateur écrit le code essentiel**, puis je relis et je débloque. Pas d'implémentation du cœur à sa place, sauf demande explicite. Le boilerplate et la config, ça va.
- **Les choix techniques lui appartiennent.** Quand je relis, je juge son approche selon ses propres termes : bugs, cas limites, conséquences. Je ne ramène pas ses choix vers ma solution préférée. Les alternatives se proposent, elles ne s'imposent pas.
- En revue, toujours exécuter le code (un petit script ou les tests) avant de conclure.

## Outils

- `uv sync` pour installer, `uv run testsuite` pour lancer les tests (les arguments sont transmis à pytest). La CI lance `ruff format --check`, `ruff check` et la testsuite.
- `uv run qiskit2pulser [f.dot] [--show]` : circuit de démo → DAG → DOT/PNG (voir le README).
- Le code est dans `src/qiskit2pulser/`, les tests dans `tests/`, les notes de conventions (Typst) dans `formalisations/`.

## État actuel

<!-- À mettre à jour à chaque réponse : 3 à 5 lignes max, on remplace au lieu d'ajouter. Pas de « prochaines étapes » : c'est l'utilisateur qui les fixe. -->
- Branche `3-convert-quantum-circuit-into-dag` : DAG maison fonctionnel (X/Y/Z/CZ, successeurs par qubit `dict[int, Node]`, `first_gate`/`last_gate`, `entries`, noms attribués par le DAG). L'étape Pulser n'existe pas encore.
- Tests : le générateur aléatoire est dans `tests/circuit_generator.py` (0 qubit accepté), et la fixture `checker` est dans `tests/conftest.py` (portée module, `CASES` = 6 cas limites (dont `(1, 2000)`) + 50 tailles tirées par la graine, ids `seedS-qN-gM`). `DAGChecker` est dans `tests/DAG/dag_checker.py`, avec un test par invariant. 168 tests au vert, et le bug volontaire `has_pred` est détecté par `test_entries`.
- `_get_all_nodes` utilise maintenant une pile explicite (à sa demande) : plus de `RecursionError`, et `(1, 2000)` passe.
- 2026-10-11 : tout est commité (`9407930`), et les 3 contrôles de la CI passent en local (lint, format, 168 tests). Piste non décidée : des prédécesseurs stockés.
