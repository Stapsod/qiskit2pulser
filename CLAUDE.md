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
- `bfs` : testé sans doublon et exhaustif (référence : `qc.data`). L'ordre topologique n'est pas garanti par l'implémentation actuelle et n'est pas testé. Reporté, sans doute à l'étape suivante.
- `to_dot_string` : testé contre le DAG (nœuds, arêtes, arêtes pointillées qubit → première porte). Arêtes comptées en multiensemble : une arête par fil de qubit, donc deux CZ successives sur la même paire donnent deux flèches. Ce comportement est figé par le test, à revoir s'il ne convient pas.
- Testsuite solveur, son ordre : d'abord `Layout` contre une référence indépendante (voisinages par force brute sur les paires, grille complète dans le disque), puis la correction du solveur avec `Layout` comme oracle. Complétude (force brute sur petite grille) reportée. Point à couvrir : un UNSAT fait passer le test de correction, donc exiger SAT sur quelques instances sûres.
- Restent : des tests pour `PySAT`, et `SolverParameters.pulser_parameters`, que personne ne lit.

### 2026-11-04
- Tests de `Layout` sur `xxx-create-layout` (branche partie de `main`). `layout.py` importait `PulserParameters`, qui n'existe que sur `8-sat-…`. La méthode s'appelle `convert_to_register`, pas `convert_to_pulser`.
- Construire `Layout` sans config pour les tests. Pistes vues : plusieurs constructeurs via `@classmethod`, ou une `@dataclass` avec `__post_init__`.
- Son choix : `LayoutParameters` (`parameters/layout_parameters.py`), une `@dataclass` simple (step, max_radius, min_dist, threshold) que `Layout` reçoit. Invariants géométriques dans `__post_init__`. La conversion `from_pulser` sera dans `LayoutParameters` (`layout/` dépend de `parameters/`), et `threshold ≤ R_b(Ω)` reste dans `PulserParameters`.
- Son idée : une hiérarchie Pulser > Layout > Solver, comprise comme une règle de dépendance (un niveau n'importe que ceux au-dessus de lui). Il s'agit de composition et de conversion, pas d'héritage.
- `PulserParameters` et `config.toml` restent sur `8-sat-…` (reset volontaire ici). `from_pulser` est commenté en attendant la fusion.
- Validation de `LayoutParameters` : `step`, `max_radius` et `min_dist` strictement positifs, et `threshold ≥ min_dist`. Relu et exécuté, ruff au vert.

### 2026-11-05
- Tests de `Layout` (à sa demande, c'est moi qui les écris) : oracle en force brute, indépendant du stencil. Grille et `distance` couvertes. Restent : voisinages, `too_close_pairs`, `convert_to_register`, validation de `LayoutParameters`.
- Bug : `int(max_radius // step)` sous-estime en flottants (`0.5 // 0.1 == 4.0`), des points du bord manquent. Même risque pour `int(threshold // step)`. Marqué `xfail(strict=True)`.
- Correctif envisagé : longueurs entières au 10⁻⁶ µm (`COORD_PRECISION` de Pulser), comparaisons sur distances² entières. Ouvert : où convertir, paramètres non multiples de 10⁻⁶. Limite : le test de rayon de Pulser est sans tolérance.
- Son choix d'ordre : `xxx-create-layout` mergée avec le bug, tests de `PySAT` sur `8-sat-…`, puis correctif depuis `main`. Tests SAT à pas entiers.
- `main` : `Layout` recevait une `PulserParameters` (duck typing). Il passe maintenant par `LayoutParameters.from_pulser_parameters`.
- Son choix : `SolverParameters` devient une `@dataclass` simple (`type`, `name`, `layout`, `dag`) avec `from_config`, et `pulser_parameters` est retiré.
- n = 0 : `PySAT` plante (littéral 0 dans `_minimal_distance`). Son choix : un circuit vide doit lever une exception, mais c'est un détail non bloquant, donc pas de test dédié. Le cas est retiré de la testsuite.
- Tests de `PySAT` : correction de la sortie (oracle `Layout`, paires CZ lues dans `qc.data`), réponses SAT/UNSAT attendues sur des cas connus, circuits aléatoires. Une mutation montre que l'absence de « au plus un emplacement par qubit » est peu détectée, car le décodage masque le problème. Complétude par force brute : reportée, il jugera plus tard si elle est utile.
- Branche `15-transpose-gates-into-pulse`. Relecture de `Gate.py` :
  - `pulse()` est abstraite, donc `Gate_Y`, `Gate_Z` et `Gate_CZ` ne sont plus instanciables, et la testsuite plante dès la collecte ;
  - Z vaut `phase_shift(π)` et non π/2 (π/2 donne S) ;
  - H n'est pas une simple impulsion π/2 ;
  - dans le commentaire de la CZ, les π sur le contrôle doivent passer par `rydberg_local` et non par une X `raman` ;
  - avec une Blackman, durée ≠ aire/Ω, car le pic vaut ≈ 2,4 × la moyenne (π en 500 ns : pic de 15 rad/µs). Pour la CZ, c'est le pic qui doit rester ≤ Ω, sinon R_b(pic) < seuil du SAT.
- Y : Y ≃ R_y(π) = R(π, π/2), soit une impulsion d'aire π et de phase −π/2. Expliqué à sa demande.
- Ses choix : `convertion(seq: Sequence)`, puisque chaque porte connaît ses qubits ; Ω passé au DAG puis aux portes pour calculer les durées.
- Points relevés :
  - le DAG est construit avant le chargement des paramètres dans `main`, et le SAT n'a pas besoin d'Ω ;
  - l'id Pulser `q{i}` est codé dans `convert_to_register`, donc deux endroits doivent rester d'accord ;
  - `area / omega` est en µs alors que Pulser attend des ns entières, multiples de 4 et ≥ 16 ;
  - `pulse()` est toujours abstraite, et la testsuite plante.
- Son idée : une IR Pulser qui porte `PulserParameters`, la `Sequence`, la création des impulsions et un dict qubit → identifiant. `_pulse` sort de `Gate`. Ouvert :
  - qui décide des impulsions : la porte, qui appelle des primitives de l'IR, ou l'IR, qui fait le dispatch sur le type de porte ;
  - la source de vérité des identifiants, aujourd'hui `convert_to_register`.
- Son option C, un contrat : chaque porte renvoie une liste d'instructions abstraites (canal, qubit, aire, phase ; phase_shift), sans dépendre de Pulser, et l'IR Pulser les exécute (durée, forme, unités, ciblage, identifiants). Ouvert : le vocabulaire d'instructions, et la façon de nommer le canal sans Pulser.
- Son choix : `PulserBackend` (`backend/pulser_backend.py`), dans l'idée d'avoir d'autres backends plus tard. Il construit les identifiants `q{i}`, le `Register` et la `Sequence`, ce qui fait de lui la source de vérité des identifiants. `Layout.convert_to_register` renvoie désormais des coordonnées, et `Layout` ne dépend plus de Pulser.
- Relecture : `qubits_id` est un `dict_keys`, alors que les portes auront besoin de passer d'un indice à un identifiant. Restent les erreurs ruff (imports inutilisés, `omega` non défini dans `Gate`) et la testsuite cassée par `pulse()` abstraite.
- Corrections faites : `qubits_id` est devenu `{i: "q{i}"}`, `convert_to_register` est renommée `get_positions`, `pulse()` n'est plus abstraite et `_pulse` est passé dans le backend. La testsuite et la démo passent. Restent 6 erreurs ruff, que la CI refusera.
- `_pulse` lève `ValueError` : la durée calculée vaut 0,05, car l'expression est en µs alors que Pulser attend des ns. L'impulsion utilise aussi `max_omega` et non l'Ω de config. Le pic de la Blackman reste à traiter.
- Son choix (sur ma proposition, implémentée par moi à sa demande) : deux Ω, qui désignent tous deux le pic d'amplitude.
  - `omega` (config) fixe les impulsions `rydberg_local` et R_b, donc le seuil SAT.
  - `omega_raman` (optionnel dans `[pulser]`, par défaut le `max_amp` de `raman_local`, vérifié) ne fixe que la vitesse des portes à 1 qubit.
  - Forme : Blackman partout. Durée : `BlackmanWaveform.from_max_val(Ω, aire)`, arrondie au multiple supérieur de `clock_period`, avec au moins `min_duration`, ce qui garde le pic ≤ Ω (`PulserBackend._duration`).
  - Exemples : π en raman = 124 ns, π en rydberg à Ω = 2 rad/µs = 3744 ns.
- Formalisation `formalisations/pulses/pulses.typ` (recette `just pulses`) : choix sur Ω, forme et durée, table des portes. Vérifiée dans l'émulateur : X, Y, Z et H sont exactes, avec une erreur < 1e-5.
- Trouvé : l'erreur de la CZ croît avec d (8,6e-4 à 4 µm, 0,20 à 10 µm, 0,43 à 11,8 µm = R_b(2)). Le seuil par défaut `threshold = R_b(Ω)` donne donc des CZ fausses. Ouvert : un seuil ou une marge selon l'erreur tolérée.
- Loi mesurée : erreur CZ ≈ 0,57·(d/R_b)⁶ (Blackman, émulateur idéal). Seuil pour une erreur ε : R_b·(ε/0,57)^(1/6). À Ω = 2 rad/µs, 1 % donne ≈ 6 µm et 0,1 % donne ≈ 4,1 µm (presque min_dist). Son choix : baisser le threshold, valeur pas encore fixée.
- Contrats, phase théorique. Son idée : des contrats propres à chaque backend, chaînés en liste, des objets simples derrière une interface commune, et dans le backend un traducteur par type de contrat. Points relevés :
  - qui produit les contrats propres au backend ? Si ce sont les portes, elles dépendent de chaque backend ;
  - à quel niveau se place le contrat : porte native (R(θ,φ), R_z, CZ), commune à tous les backends, ou impulsion, propre aux atomes neutres ;
  - précision de sa part : la liste chaînée est propre à chaque porte (nœud du DAG). Le DAG reste la structure globale, donc le parallélisme est conservé.
- Son choix : les portes se décomposent en opérations natives communes à tous les backends (rotations), et chaque backend les interprète. Pour Pulser, c'est `PulserBackend` qui traduit en canal, aire et phase.
- Son choix : le vocabulaire des contrats, ce sont les opérations natives { R(θ, φ), R_z(φ), CZ(a, b) }, et la CZ est un contrat comme les autres. Le backend traduit chaque contrat en une ou plusieurs instructions (pour Pulser : CZ → 3 impulsions `rydberg`). Proposé mais pas tranché : la convention de Qiskit dans les contrats (le −φ vit dans `PulserBackend`) et une CZ symétrique (l'orientation est choisie par le backend).
- Contrats implémentés par moi à sa demande. Des `dataclass(frozen=True)` `R`, `Rz` et `CZ` dans `utils/contracts.py`, plutôt que sa liste chaînée avec un enum de type : une `list` suffit tant qu'aucune passe ne réécrit les chaînes. `Gate.contracts()` remplace `convertion`, et H est ajoutée à `_gate_types`.
- `PulserBackend` :
  - `translate`, un `match` par contrat, avec le −φ, le `phase_shift` en base digital et la CZ π–2π–π ;
  - `build(dag)` ;
  - les canaux sont déclarés à leur première utilisation.
- `DAG.topological` (Kahn) a été ajouté, car le `bfs` sortait `cz1` avant ses prédécesseurs. Il est testé.
- Vérifié de bout en bout dans l'émulateur : erreur < 3e-5 sur les circuits aléatoires, et la CNOT comme l'état de Bell construits avec la CZ sont corrects. La formalisation `pulses.typ` est à jour.
- Prochaine séance, à sa demande : nettoyer `__init__.py`. Restent aussi : le seuil CZ (la démo place sa CZ à 10,2 µm, soit ≈ 20 % d'erreur), le correctif des flottants de `Layout`, et la vérification par l'émulateur, qui n'est pas dans la testsuite.

### 2026-11-06
- `config.toml` : `threshold = 6.0` (≈ 1 % d'erreur CZ d'après la loi mesurée).
- `__init__.py` nettoyé. Son choix : une classe `Compiler` (`compiler/compiler.py`, d'abord nommée `Qiskit2Pulser`) et `CompilerParameters`, qui dépend encore d'un `argparse.Namespace`.
- Modularité des backends (issue 18), son objectif : pouvoir ajouter d'autres backends, sans Pulser dans `__init__.py`. Pour l'instant, seule la fin de la chaîne est traitée, avec le même système que `Solver` (classe mère + factory).
- Reporté : placer le SAT et `Layout` derrière le backend. `Compiler` les importe encore, or le placement est propre aux atomes neutres.
- Exécution directe : sa piste de départ était de renvoyer une bitstring. Il faut plutôt des résultats sur N shots, et garder la compilation seule, car l'émulation est limitée à peu de qubits (3 niveaux par atome).
- Résultat d'exécution, proposé, pas tranché : `counts`, `shots`, nom du backend et `metadata` propres au backend. Comptages plutôt que probabilités (qui s'en déduisent). Pas d'état final dans le contrat commun.
- Contrat proposé : tous les qubits mesurés à la fin, bit i = qubit i, ordre de Qiskit (q0 à droite). Ordre de Pulser à vérifier. Les `qc.measure` partiels viendront plus tard.
- En cours, son début d'implémentation : étapes de `Compiler` rendues privées, `build()` et `run(shot) -> CompilerResult` (`utils/compiler_result.py`), encore vides pour `run` et `CompilerResult`.
- Restent : l'accès au programme compilé, un second `build` du backend qui double la séquence (`PulserBackend` accumule dans `self.sequence`), une valeur par défaut de `shots` dans la config, et le README, qui annonce encore l'affichage du circuit et du DAG.
- Système de backends, ses choix : classe mère `Backend` (`build`, `translate`, `run(shots) -> CompilerResult`), `make_backend(parameters)` + dict `available_backend` (`backend/backend_factory.py`), `BackendParameters.type` pour choisir la sous-classe.
- `CompilerResult` : `counts`, `shots`, `backend_name`, `metadata`.
- Son choix : les positions passent par les paramètres (`PulserParameters.add_positions`), et le backend ne reçoit plus que `parameters`.
- Création du backend dans `Compiler`, son choix : section `[backend]` de la config, `make_backend_parameters(config_path)` à côté de `make_backend`, `BackendParameters` dans son propre fichier avec `positions`/`add_positions`. `LayoutParameters.from_pulser_parameters` reste le seul lien avec Pulser tant que le placement n'est pas derrière le backend.
- Avant de merger `18-add-modularity-to-handle-multiple-backend` : remplir `CompilerResult` et exécuter les séquences dans `PulserBackend.run`, qui renvoie encore un résultat vide.

### 2026-11-08
- Vérifié dans Pulser 1.9.1, pour `PulserBackend.run` :
  - `sample_final_state` met q0 à gauche, donc à l'inverse de Qiskit (q0 à droite) ;
  - sans `measure`, une séquence raman + rydberg est échantillonnée en base digital ;
  - un second `measure` lève `RuntimeError`, et la séquence n'est plus modifiable après `measure` ;
  - l'émulateur refuse une séquence sans impulsion (`ValueError`), ce qui arrive pour un circuit sans porte ou avec seulement des Z.
- `PulserBackend.run` : bitstrings inversées pour suivre l'ordre de Qiskit.
- Son choix : `measure` passe à la fin de `build`, et `build` vérifie d'abord que `self.sequence` vaut `None` (un second `build` lève une erreur ou ne fait rien).
- Ouvert : un circuit avec seulement des CZ plante à l'émulation (`measure("digital")` sur une simulation `ground-rydberg`).
- Modularité, verrou : `Compiler` impose `Layout` + SAT, et `positions` est dans `BackendParameters`.
- Sa piste, non tranchée : une liste d'actions propre à chaque backend (pour Pulser, le placement). Il faut alors une interface d'exécution commune et un contexte partagé (les positions passent d'une action à l'autre).
- Alternative, non tranchée : le placement dans `PulserBackend.build`. Critère : quelqu'un hors du backend doit-il voir les étapes ?
- Les deux pistes sont reportées : pas d'autre backend prévu avant un moment.
- Sa piste pour la testsuite : comparer les `CompilerResult` de Pulser à Qiskit, avec une tolérance. Tolérance à fixer selon n, les shots et le nombre de CZ (biais physique ≈ 1 % par CZ à 6 µm).
