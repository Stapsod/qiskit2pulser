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

<!-- À mettre à jour à chaque réponse : 3 à 5 lignes max, on remplace au lieu d'ajouter. Pas de « prochaines étapes » : c'est l'utilisateur qui les fixe. -->
- Branche `3-convert-quantum-circuit-into-dag` : Qiskit → DAG maison fonctionnel (portes X/Y/Z/CZ, successeurs, première et dernière porte par qubit, noms attribués par le DAG).
- Outillage : `uv run qiskit2pulser [f.dot] [--show]` (circuit de démo → DAG → DOT/PNG), documenté dans le README. La feuille de route du README a été remplacée par un « État d'avancement », sans étapes futures. L'étape Pulser n'existe pas encore.
- Testsuite du DAG : l'utilisateur a choisi un générateur de circuits aléatoires + des invariants (pas d'oracle Qiskit). Il implémente d'abord le générateur, à partir de mes explications : `random.Random(seed)`, portes tirées de `_gate_types`, arité donnée par `get_standard_gate_name_mapping()`, `rng.sample` pour les qubits, `parametrize` sur les graines.
- Rien n'est commité depuis `07af239`.
