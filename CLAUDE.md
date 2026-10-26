# qiskit2pulser

Projet perso d'apprentissage : un compilateur qui prend un `QuantumCircuit` Qiskit et produit une `Sequence` Pulser (atomes neutres). D'abord le mode digital (portes → impulsions), le mode analogique viendra plus tard.

## Comment travailler avec l'utilisateur

- On échange en français, mais les commentaires et docstrings du code sont en anglais.
- Mode mentorat : j'explique les concepts et fixe l'objectif de chaque étape. **L'utilisateur écrit le code essentiel**, puis je relis et je débloque. Pas d'implémentation du cœur à sa place, sauf demande explicite. Le boilerplate et la config, ça va.
- **Les choix techniques lui appartiennent.** Quand je relis, je juge son approche selon ses propres termes : bugs, cas limites, conséquences. Je ne ramène pas ses choix vers ma solution préférée. Les alternatives se proposent, elles ne s'imposent pas.
- Placement des atomes : aucune piste d'implémentation de ma part, sauf demande explicite (règle qu'il a posée le 2026-10-12).
- En revue, toujours exécuter le code (un petit script ou les tests) avant de conclure.
- **Je tiens l'entrée du jour de l'Historique à jour moi-même, dès qu'un choix est pris ou qu'une piste est ouverte ou écartée, sans attendre qu'il le demande.** Quelques puces courtes et techniques : choix, pistes gardées pour plus tard, pistes explorées, questions ouvertes. Pas de récit de séance.

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
- Formalisme : la justification des implications à sens unique de s et t (équisatisfiabilité) est rédigée dans `clauses.typ`. Ω et le seuil deviennent des paramètres.
- Analyse neutre du formalisme. La logique est juste. Les points qui comptent pour Pulser :
  - le disque est relatif à l'origine du `Register` (`from_coordinates` recentre, mais pas `Register(dict)`) ;
  - les CZ passent par `rydberg_local`, ce qui justifie l'absence de contraintes sur les spectateurs.
- Alternatives au SAT (MaxSAT, ILP/CP-SAT, heuristiques) consignées dans `formalisations/SAT/alternatives/alternatives.typ`. Le SAT reste la piste suivie.
- Reportés : les tests préliminaires et tout ce qui touche à l'UNSAT et au routage. Une phase d'optimisation du circuit est prévue avant le DAG.
- Début du dev, son archi :
  - un main enchaîne circuit → DAG → paramètres → SAT → `Register` ;
  - l'encodage ne voit que des paramètres (repère abstrait) ;
  - les clauses sont envoyées au fil de l'eau ;
  - une classe mère abstraite pour le solveur, avec une sous-classe par solveur.
- Paramètres, en quatre catégories :
  - constantes du device, lues dans Pulser ;
  - choix de config (Ω, pas, marge du seuil) ;
  - valeurs dérivées (R_b(Ω) → seuil → P, D, N(p)) ;
  - valeurs qui dépendent du circuit (n, C).

  Ω vaut pour tout le compilateur, impulsions CZ comprises. Il prévoit un fichier de config.
- `RegisterLayout` : Pulser impose 4 µm entre les pièges, donc un layout au pas de 2 µm est refusé. Le gain en clauses vient du pas (au pas de 4 : plus de famille 4, ≈ 10× moins de littéraux pour la famille 5, mais un degré CZ max de 8). Pas encore tranché, le paramètre « pas » couvre les deux cas.
- Code : il a lancé `PulserParameters` (`utils/pulser_parameters.py`) et la classe mère `Solver` (`SAT/utils/solver.py`). À sa demande, j'ai complété `PulserParameters` : les constantes sont lues dans le device, omega/step/threshold viennent de la section `[pulser]` de `config.toml` (threshold vaut R_b par défaut), et la cohérence est vérifiée.

### 2026-10-19
- Solveur en boîte noire : le `main` donne paramètres Pulser + infos du circuit, récupère un arrangement. Classe mère abstraite gardée, une seule sous-classe PySAT (CaDiCaL visé). On reste sur SAT, alternatives plus tard.
- Numérotation : les x occupent les n·P premiers entiers (formule inversible, rien à stocker), auxiliaires ensuite, non décodées.
- Grille : carrée, centrée sur l'origine, coupée au disque (distance à l'origine ≤ `max_radial_distance`, comme Pulser). Pas de 2 : P = 1961, pas de 4 : P = 489.
- La grille devient une abstraction du registre (`Layout`, dans `layout/`) qui portera de la logique métier, plutôt qu'une classe de paramètres. Nom retenu : `Layout`, malgré `qiskit.transpiler.Layout`.
- Archi par étape : `DAG/`, `parameters/`, `solvers/`, `layout/`.
- `Layout` porte toute la logique géométrique (distance, trop proche si d < `min_dist`, à portée de CZ si `min_dist` ≤ d ≤ `threshold` de la config) ; le solveur s'en sert pour D et N(p).
- Géométrie sans P² paires : choix du motif de décalages (stencil), qui exploite la régularité de la grille. Voisinages précalculés à l'init. KD-tree (`cKDTree`) gardé en réserve si la grille cesse d'être régulière.
- Ouvert : `nb_qubits` dans `SolverParameters` mais `cz` en argument d'`encode`.

### 2026-10-24
- Quelles portes alimentent C : son critère physique est « le qubit passe-t-il en Rydberg, et avec qui ». En digital, ça n'arrive que dans une CZ, à condition que le circuit soit en base native (SWAP, Toffoli… décomposés avant), que les CZ passent par `rydberg_local` et qu'elles restent sérialisées.
- En analogique (plus tard), Rydberg global : le critère ne se limite plus aux paires des CZ.
- Extraction des CZ : le DFS récursif dans `PySAT.__post_init__` est juste, mais lève `RecursionError` dès ≈ 1000 portes sur un chemin. Son choix : un BFS générique dans `DAG`, avec une fonction passée en paramètre.
- Point à garder en tête : un BFS depuis les entrées ne garantit pas l'ordre topologique (cf. l'idée des prédécesseurs du 11).
- Test préliminaire, sa variante : lancer le SAT sans la famille 5 (CZ). Point relevé : avec n ≤ 100 et un pas ≤ 4 µm, la grille contient toujours une sous-grille de pas ≥ 4 µm d'au moins 100 points (489 au pas de 2), donc ce test est toujours SAT et se réduit à vérifier n ≤ `max_atoms`. Pas tranché.
- Numérotation : retour aux décalages sans stockage (choix du 19). x, s, t contigus à partir de 1. t est indexé (p, j) avec un pas de n.
- Clauses 1 à 5 implémentées dans `PySAT` en suivant `clauses.typ`. Vérifiées par force brute sur de petites instances et sur la vraie grille (P = 1961).
- Cycle de vie du solveur : `with`. `Solver.__enter__` appelle `_enter` (construction des variables et des clauses), et nettoie lui-même en cas d'échec, puisque `__exit__` n'est pas appelé dans ce cas. `_delete` accepte `solver is None`.
- Interface de `Solver` : `solve() -> bool`, `get_solution() -> list[int]`, `_enter`, `_delete`.
- Sortie du solveur : il renvoie un indice d'emplacement p par qubit (décodage des x dans la sous-classe, car la numérotation lui est propre). `Layout` traduit p → coordonnées → `Register`.
- Pour le `Register` : `from_coordinates` recentre par défaut (`center=True`), ce qui peut sortir un atome du disque. Garder `center=False`, ou `Register(dict)`.
- Restent : `Layout.convert_to_pulser`, des tests pour `PySAT`, `bfs` et `to_dot_string`, et `nb_qubits` qui est à la fois dans `SolverParameters` et lu dans le DAG (`dag.num_qubits`).

### 2026-10-26
- `SolverParameters` n'était lue par personne (géométrie via `Layout`, n et C via le DAG). Son choix : elle devient la config du solveur, lue dans la section `[SAT_solver]` de `config.toml` (`type`, validé contre une liste de solveurs supportés). `nb_qubits` en sort.
- Classe factory jugée superflue (elle doublait le protocole `with` de `Solver`). Son choix : une fonction `make_solver(parameters)` et un dict `{type: sous-classe}` qui sert aussi de liste des solveurs supportés. Le solveur renvoyé n'est pas encore entré.
- `PySAT` est gardée : la CNF ne dépend pas du solveur choisi. Config `[SAT_solver]` : `type` choisit la sous-classe de `Solver`, `name` choisit le solveur PySAT (`cadical195`…). Une nouvelle sous-classe ne se justifie que pour un autre backend (CP-SAT, binaire DIMACS).
- Son choix : `SolverParameters` porte aussi `layout` et `dag`, et `Solver` ne prend plus qu'elle en argument.
- `make_solver` et le dict sont dans `solvers/solver_factory.py` (dans `solver.py`, ils créaient un import circulaire avec `PySAT`). Imports uniformisés en `qiskit2pulser.` (le préfixe `src.` chargeait les modules en double).
- `Layout.convert_to_pulser(positions)` : `Register(dict)` sans recentrage, identifiants `str` `q{i}` (i = indice du qubit Qiskit ; les `int` sont dépréciés dans Pulser 1.9). Pas de validation contre le device dans `Layout`, `Sequence` revalide.
- Vérifié dans Pulser 1.9.1 : `DigitalAnalogDevice.requires_layout` vaut `True`, mais un `Register` sans `RegisterLayout` est accepté par `Sequence`. Le pas de 2 µm reste donc possible.
- Testsuite SAT, deux propriétés : correction (une solution SAT respecte les contraintes, via un oracle indépendant de `Layout`) et complétude (pas d'UNSAT sur une instance faisable). Il faut des instances dont la réponse est connue et de petites grilles. Rien de tranché.
- `bfs` : testé sans doublon et exhaustif (référence : `qc.data`). L'ordre topologique n'est pas garanti par l'implémentation actuelle et n'est pas testé ; reste à décider si `bfs` doit le promettre.
- Restent : des tests pour `PySAT` et `to_dot_string`, et `SolverParameters.pulser_parameters`, que personne ne lit.
