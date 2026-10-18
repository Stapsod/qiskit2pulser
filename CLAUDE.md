# qiskit2pulser

Projet perso d'apprentissage : un compilateur qui prend un `QuantumCircuit` Qiskit et produit une `Sequence` Pulser (atomes neutres). D'abord le mode digital (portes → impulsions), le mode analogique viendra plus tard.

## Comment travailler avec l'utilisateur

- On échange en français, mais les commentaires et docstrings du code sont en anglais.
- Mode mentorat : j'explique les concepts et fixe l'objectif de chaque étape. **L'utilisateur écrit le code essentiel**, puis je relis et je débloque. Pas d'implémentation du cœur à sa place, sauf demande explicite. Le boilerplate et la config, ça va.
- **Les choix techniques lui appartiennent.** Quand je relis, je juge son approche selon ses propres termes : bugs, cas limites, conséquences. Je ne ramène pas ses choix vers ma solution préférée. Les alternatives se proposent, elles ne s'imposent pas.
- Placement des atomes : aucune piste d'implémentation de ma part, sauf demande explicite (règle qu'il a posée le 2026-10-12).
- En revue, toujours exécuter le code (un petit script ou les tests) avant de conclure.

## Outils

- `uv sync` pour installer, `uv run testsuite` pour lancer les tests (les arguments sont transmis à pytest). La CI lance `ruff format --check`, `ruff check` et la testsuite.
- `uv run qiskit2pulser [f.dot] [--show]` : circuit de démo → DAG → DOT/PNG (voir le README).
- Le code est dans `src/qiskit2pulser/`, les tests dans `tests/`, les notes de conventions (Typst) dans `formalisations/`.

## Historique

<!-- Une entrée par jour de travail, la plus récente en bas. Chaque entrée dit ce qui a été fait, décidé ou laissé ouvert. Rester bref et garder le fichier lisible, sans jamais perdre d'information utile. Le jour même, on complète l'entrée. On ne touche pas aux jours passés. Pas de « prochaines étapes » : c'est l'utilisateur qui les fixe. -->

### 2026-10-08
- Démarrage : notebook d'essai Qiskit, premières classes `Gate` et `DAG` (simple liste au départ), début du convertisseur.

### 2026-10-10
- Une classe par porte (dataclass), `add_gate` et export DOT, ajout de la CZ.
- `main` de démo (circuit → DAG → DOT/PNG), sorties dans `out/`.

### 2026-10-11
- Successeurs stockés dans un dict par qubit. Testsuite : générateur aléatoire de circuits, `DAGChecker` (parcours non récursif), conftest et cas limites codés en dur.
- CI de lint. 168 tests au vert sur `5-create-a-testsuite-for-the-dags`, pas encore mergée dans `main`. Idée non tranchée : stocker aussi les prédécesseurs.

### 2026-10-12 (et séances suivantes, dates non notées)
- Il attaque le placement des atomes avant les impulsions. Contraintes `DigitalAnalogDevice` : 2D, distance min 4 µm, rayon 50 µm, 100 atomes, R_b ≈ 6,6 µm à Ω max.
- Ses choix : CZ sérialisées (invariant à respecter dans la `Sequence`), solveur SAT, grille de pas ≈ 2 µm (P ≈ 2000), x[q][p], couronne CZ ¬x[a][p] ∨ ⋁_{N(p)} x[b][p'] (4 µm ≤ d ≤ seuil), UNSAT ⇒ routage.
- Distance min : il est passé de ≈ 128 M de clauses par paire de qubits à o[p] = « p occupé » (liaison x → o, ¬o[p] ∨ ¬o[p'] pour p ≠ p').
- Cassage de symétrie (fixer un qubit) : gain jugé faible. Qubits « pivots » : idée mise de côté.

### 2026-10-17
- Comptage : ≈ 192 M de clauses, presque toutes venant du « au plus un emplacement par qubit » encodé par paires. Trou repéré : rien n'empêchait deux qubits sur le même p.
- Sa piste y[q] (« placé quelque part ») ne marche pas : un OU ne compte pas. À sa demande, je lui ai donné le compteur séquentiel (Sinz) pour les deux « au plus un » (≈ 1,4 M + m·P au total).
- Son idée : retirer o, car le compteur t le rend redondant. Piège signalé : t[p][n−2] ne couvre pas le dernier qubit. Son correctif : une colonne t[p][n−1] = « p occupé », qui remplace o[p] et rend la liaison x → o inutile (total ≈ 1,18 M + m·P).
- Exercice papier fait : UNSAT par manque de place, même sans CZ. Sa règle « UNSAT ⇒ routage » ne tient donc pas en général.
- Son choix : des tests préliminaires avant le SAT, dont un placement trivial sans tenir compte des CZ. S'il passe, la géométrie est faisable et un UNSAT vient des CZ (donc routage). Restent ouverts : que faire s'il échoue, quel placement trivial choisir, pourquoi les implications dans un seul sens suffisent. Rien n'est codé.
- Le formalisme complet (variables, clauses, comptage, questions ouvertes) est rédigé dans `formalisations/SAT/clauses/clauses.typ`.

### 2026-10-18
- Tests préliminaires (placement trivial, que faire s'il échoue) : reportés à plus tard à sa demande. Priorité aux clauses.
- Implications à sens unique : son raisonnement (s et t servent à propager, le solveur essaie autre chose si une valeur est fausse), que j'ai complété par l'argument logique. Pas de faux SAT, car hors de leur chaîne, s et t n'apparaissent qu'en négatif : un s ou t mis à vrai à tort ne peut qu'interdire. Pas de faux UNSAT, car le s/t « honnête » calculé depuis x satisfait tout. Ça ne tient que tant qu'aucune clause n'utilise t en positif. Question ouverte résolue et rédigée à sa demande dans `clauses.typ` (section « Pourquoi un seul sens suffit »).
- Seuil de la couronne = distance max pour que le blocage fonctionne, donc ≤ R_b(Ω). Son choix : Ω et le seuil sont deux paramètres variables.
- Analyse neutre du formalisme à sa demande. La logique est juste. Points soulevés :
  - cohérence Pulser : `from_coordinates` recentre par défaut, et le rayon de 50 µm est testé sans tolérance ;
  - hypothèse non écrite : CZ via `rydberg_local` ;
  - toutes les distances de la couronne se valent (fidélité) ;
  - grille ≠ continu ;
  - placement en tout-ou-rien, et rien sur le problème après routage ;
  - nombre de littéraux de la famille 5, et m ≤ 4950 irréaliste ;
  - symétries sur les instances UNSAT ;
  - doc pas à jour sur Ω/seuil.
- Il demande ce qui bloque le dev. Mon avis : l'idée tient, sans bloquant de fond pour le module SAT. Deux décisions restent à écrire : le repère du disque face au recentrage du `Register`, et l'hypothèse CZ via `rydberg_local`. Le vrai trou est global : le comportement après un UNSAT (routage), qu'il assume de reporter ou non.
- Il demande s'il y a mieux que le SAT. Pistes présentées à sa demande : MaxSAT (CZ en clauses souples), ILP/CP-SAT (objectif, cardinalités natives), heuristiques (greedy, force-directed). Mon avis : pas de « meilleur » absolu, le SAT tient pour son objectif. Sa faiblesse est le tout-ou-rien. Rien n'est tranché. À sa demande, c'est consigné dans `formalisations/SAT/alternatives/alternatives.typ` (recette `just SAT_alternatives`), au cas où le SAT ne serait pas intéressant.
