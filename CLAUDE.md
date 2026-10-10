# qiskit2pulser

Projet perso d'apprentissage : un compilateur qui prend un `QuantumCircuit` Qiskit et produit une `Sequence` Pulser (atomes neutres). D'abord le mode digital (portes → impulsions), le mode analogique viendra plus tard. La feuille de route est dans le README.

## Comment travailler avec l'utilisateur

- On échange en français.
- Mode mentorat : j'explique les concepts et fixe l'objectif de chaque étape. **L'utilisateur écrit le code essentiel**, puis je relis et je débloque. Pas d'implémentation du cœur à sa place, sauf demande explicite. Le boilerplate et la config, ça va.
- **Les choix techniques lui appartiennent.** Quand je relis, je juge son approche selon ses propres termes : bugs, cas limites, conséquences. Je ne ramène pas ses choix vers ma solution préférée. Les alternatives se proposent, elles ne s'imposent pas.
- En revue, toujours exécuter le code (un petit script ou les tests) avant de conclure.

## Outils

- `uv sync` pour installer, `uv run testsuite` pour lancer les tests (les arguments sont transmis à pytest).
- Le code est dans `src/qiskit2pulser/`, les tests dans `tests/`, les notes de conventions (Typst) dans `formalisations/`.

## État actuel

<!-- À mettre à jour à chaque réponse : 3 à 5 lignes max, on remplace au lieu d'ajouter. -->
- Branche `3-convert-quantum-circuit-into-dag` : conversion du circuit Qiskit vers une structure de DAG maison.
- Dernière revue : les bugs de détail sont corrigés, mais la structure actuelle (un seul `next` par nœud) duplique les portes à plusieurs qubits. L'utilisateur revoit la structure.
- En attente : la nouvelle version du DAG et un premier test `tests/test_dag.py`.
- `CLAUDE.md` créé le 2026-10-10, pas encore commité.
