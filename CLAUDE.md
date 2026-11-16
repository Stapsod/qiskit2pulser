# qiskit2pulser

Projet perso d'apprentissage : un compilateur qui prend un `QuantumCircuit` Qiskit et produit une `Sequence` Pulser (atomes neutres). D'abord le mode digital (portes → impulsions), le mode analogique viendra plus tard.

## Comment travailler avec l'utilisateur

- On échange en français, mais les commentaires et docstrings du code sont en anglais.
- Mode mentorat : j'explique les concepts et fixe l'objectif de chaque étape. **L'utilisateur écrit le code essentiel**, puis je relis et je débloque. Pas d'implémentation du cœur à sa place, sauf demande explicite. Le boilerplate et la config, ça va.
- **Les choix techniques lui appartiennent.** Quand je relis, je juge son approche selon ses propres termes : bugs, cas limites, conséquences. Je ne ramène pas ses choix vers ma solution préférée. Les alternatives se proposent, elles ne s'imposent pas.
- Placement des atomes : aucune piste d'implémentation de ma part, sauf demande explicite (règle qu'il a posée le 2026-10-12).
- **En fin de séance, j'ajoute la durée de la conversation à la section « Temps passé » (fin du fichier) et je mets le total à jour.**
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
- Sa piste pour la testsuite : comparer les `CompilerResult` de Pulser à Qiskit, avec une tolérance. Comparaison implémentée (`tests/end2end/`) : distance en variation totale ≤ 2 × ½√(2ⁿ/N) + 1 % par CZ. Le terme de bruit donne ≈ 0,5 % de fausses alertes à n = 1 (cas uniforme, le pire).
- Tests e2e : `get_qc_and_proba(i)` sert à ajouter des circuits. Pour l'instant, seul le circuit de démo y est : il n'a pas de superposition, donc il ne détecte pas une CZ sans effet (il faut des H autour). Le 1 % par CZ est lié à `threshold = 6.0`. Tirage non seedé.
- Reportés, son choix : les circuits avec seulement une Z ou seulement des CZ, couverts par deux tests `xfail(strict=True)` dans `tests/backend/`.
- `CompilerParameters` : le constructeur prend `dot_file_path` et `show_dag` (défauts `None` et `False`), et `from_args` fait le lien avec `argparse`.
- Relevé : `QutipEmulator` est déprécié depuis Pulser 1.9 (`QutipBackendV2` à la place).
- Tests e2e : circuit 1 = état de Bell (H, H, CZ, H), `test_circuit` paramétré sur les indices. Sans la CZ, la distance vaut 0,5 pour une tolérance de 0,073 : le test détecte bien une CZ sans effet.
- Circuits aléatoires e2e écartés (son choix : overkill). À la place, deux circuits écrits à la main : H Z H (effet de la Z en superposition) et GHZ à 3 qubits (deux CZ en chaîne).
- Circuit avec seulement une Z : forcer le canal ne suffit pas, `raman_local` est déjà déclaré par la branche `Rz`. L'émulateur refuse la séquence sans impulsion (`ValueError`), et un `delay` échoue aussi (`meas_basis`).
- Son choix : sans impulsion (`sequence.get_duration() == 0`), `run` renvoie `{"0" * n: shots}` sans émuler. Couvre aussi un circuit sans porte (à n > 0).
- Circuit avec seulement des CZ : sans impulsion `raman`, la simulation est à 2 niveaux et refuse `measure("digital")`, même avec `raman_local` déclaré. `measure("ground-rydberg")` passe et donne `{'00': 1000}`.
- Son choix : le raccourci de `run` s'élargit à « aucune impulsion `raman` » (Z seules, CZ seules, Z + CZ, sans porte). Pas de `ground-rydberg`. Limite : à revoir si le bruit est simulé un jour. Implémenté par lui sur `xxx-fix-degenerate-circuits-emulation`, les deux `xfail` sont retirés.
- Optimisation (branche `23-…`), son choix : première passe sur les portes à 1 qubit, directement dans le DAG, en parcourant chaque fil de qubit et en comparant chaque porte à la précédente (X X, etc.). `DAG.reduce_unitary_gate`, corrigée par moi à sa demande : pile des portes conservées par fil, recâblage (`successors`, `first_gate`, `last_gate`) et maintien d'`entries`. Activée par `CompilerParameters.apply_opti` (vrai par défaut).
- Tests e2e de l'opti (`test_optimisation_preserves_results`, à sa demande, écrits par moi) : 7 circuits compilés avec et sans la passe, comparaison des distributions (tolérance × √2, deux échantillons) et nombre exact de portes restantes. Testsuite à ≈ 50 s.

### 2026-11-12
- Avant de merger la branche 23 : ruff au vert, 717 tests passés + 1 xfail (flottants de `Layout`). `reduce_unitary_gate` vérifiée sur 3000 circuits aléatoires (`entries`, `last_gate`, chaînes, tri topologique, nombre de portes contre une référence « pile par fil ») : aucun écart.
- README mis à jour (par moi) : pipeline, `config.toml`, exécution (`CompilerResult`), formalisations, structure, avancement. `--show` ouvre le graphe avec `feh`, codé en dur dans `Compiler._show_dot`.
- Son choix : `apply_opti` ira dans la config (pas de flag CLI `--no-opti`). Nettoyage des paramètres sur une branche dédiée, objectif : centraliser, lire `config.toml` une seule fois (aujourd'hui 3 lectures : `make_backend_parameters`, `PulserParameters`, `SolverParameters.from_config`). Sa piste, non tranchée : tout stocker dans `CompilerParameters`.
- Points relevés : les « Parameters » mélangent config, constantes du device, valeurs dérivées, options CLI et données produites (`dag`, `layout`, `positions` via `add_positions`). `step`/`threshold` sont dans `[pulser]` alors qu'ils servent au placement. Les tests construisent `LayoutParameters`/`SolverParameters` sans fichier.
- Branche `xxx-clean-parameters`. Son choix : revoir le découpage des paramètres, en commençant par sortir `Layout` de `Compiler`. Comme le SAT dépend de `Layout`, le placement suit, dans `PulserBackend.build`. Une classe mère `ColdAtomsBackend` viendrait seulement s'il y a un second backend à atomes neutres. Conséquences : `Compiler` générique, `positions`/`add_positions` sortent de `BackendParameters`, `[SAT_solver]` lue pour le backend (comment il la reçoit : ouvert), `Compiler` ne voit plus les positions. Avis demandé : découpage plus propre (frontière physique, `step`/`threshold` lus par leur utilisateur) ; vigilance : `build` chargé, positions invisibles hors backend.
- Ses choix :
  - lire `config.toml` une seule fois et passer le dict aux différents Parameters, au lieu du chemin ;
  - un Parameters = tout ce dont l'étape a besoin, pas seulement de la config (donc `layout`/`dag` dans `SolverParameters`, `qc` et options CLI dans `CompilerParameters` sont acceptés).
- Mis de côté pour l'instant : `apply_opti` en config, `"config.toml"` codé en dur dans `main`.
- Ouvert pour la lecture unique : qui lit le fichier (`main`, `Compiler` ou `CompilerParameters`), dict entier ou sections (le backend a besoin de `[pulser]` et `[SAT_solver]`), section/clé absente (aujourd'hui `KeyError` brut). `test_pulser_backend` passe un chemin à `make_backend_parameters`, à adapter. Rien n'est codé.

### 2026-11-13
- Placement déplacé par lui dans `PulserBackend` (`Layout` construit dans `__init__`, SAT dans `build`). La démo plante : `build` lit `self.parameters.config_path`, que `PulserParameters` n'a pas.
- Sa piste pour la config : `main` lit le fichier, passe le dict complet à `CompilerParameters`, et `Compiler` distribue les clés. Point relevé : si `Compiler` choisit lui-même `[pulser]`/`[SAT_solver]`, il connaît le backend, alors qu'il devait rester générique. Variante : `Compiler` ne lit que `[backend]` et le générique, et transmet le dict à `make_backend_parameters`, qui laisse la sous-classe prendre ses sections.
- Son choix : la variante. Le dict entier descend jusqu'au backend, et `PulserParameters` prend lui-même `[pulser]` et `[SAT_solver]`.
- Implémenté par lui : `main` lit le fichier (chemin en 2ᵉ argument positionnel optionnel), `PulserParameters.config` garde le dict, et `PulserBackend.build` construit `SolverParameters` depuis `config["SAT_solver"]`. La démo passe avec `qiskit2pulser x.dot config.toml`. Relevés : un seul argument est pris pour `dot_file` (plantage `None`), le SAT est relancé avant la garde « build une seule fois », `solver_parameters` n'est pas initialisé dans `__init__`, 8 imports inutilisés, `positions`/`add_positions` sont encore dans `BackendParameters`. Tests pas encore adaptés.
- Restent : corriger ces points, puis adapter les tests (un dict de config écrit en dur dans le conftest au lieu d'un chemin). `apply_opti` en config reste mis de côté.

### 2026-11-14
- `SolverParameters` dans `PulserBackend`, son choix : un attribut, initialisé à `None` dans `__init__` et construit dans `build` (le DAG n'arrive qu'à ce moment-là). L'alternative, une variable locale passée à `_solve_positions`, est écartée pour l'instant. Nettoyage prévu plus tard.
- CLI, son choix : `config_path` est un positionnel obligatoire, et le DOT passe par l'option `--dotfile` (toujours écrit dans `out/`). La garde « build une seule fois » passe avant le SAT, `positions`/`add_positions` sont retirés de `BackendParameters`. ruff check est au vert, et la démo tourne avec `qiskit2pulser config.toml`.
- Testsuite adaptée (par moi, à sa demande) : config de test écrite en dur dans `tests/config.py` (`make_config()`, un dict neuf à chaque appel, `threshold = 6.0` dont dépend `CZ_ERROR` des tests e2e), indépendante de `config.toml`. Les tests de `tests/backend/` ne forcent plus les positions, c'est le SAT qui les choisit. 717 tests passés + 1 xfail.
- README mis à jour (CLI, flux de la config, `tests/config.py`). Son choix : `apply_opti` passe en config sur cette même branche.
- `apply_opti`, son choix : dans `[compiler]` de la config, lu par `Compiler` ; retiré de `CompilerParameters` (une seule source). Clé absente : `KeyError` brut, pas de défaut. Les tests e2e modifient le dict de `make_config()`.
- Type de la config : `dict[str, dict[str, Any]]` (son choix, sans alias). `tomllib` ne garantit que `dict[str, Any]`, le premier niveau en sections est une convention du projet.
- Branche `xxx-clean-parameters` squashée dans `main`. Nouvelle branche `26-add-resource-estimation`.
- Métriques d'optimisation. Comptage de Toffoli (A&B, tolérance aux fautes) hors sujet : le jeu de portes x, y, z, h, cz est entièrement Clifford.
- Ses choix : une fonction d'estimation de ressources par backend. Pas de catégories communes : chaque backend renvoie toutes les statistiques peu coûteuses à calculer. Retour : un dict indexé par nom d'objets estimation (nom, description, unité, valeur).
- Sa proposition de métriques Pulser, pas tranchée : nombre d'atomes, nombre de CZ, nombre d'impulsions `raman`, profondeur du DAG, durée totale. Écartées : erreur CZ estimée, nombre de R_z, durée par canal, reciblages.
- Profondeur : son intérêt serait de comparer les backends. Relevé : la profondeur du DAG est la même pour tous les backends (calculée avant la traduction). Pour comparer, il faudrait la profondeur après traduction, sur les opérations natives du backend. Sinon, c'est une propriété du circuit, plutôt côté `Compiler`.
- Sa piste, non tranchée : accepter des portes non natives et les décomposer dans le DAG en portes natives, pour optimiser sur le vrai jeu de portes. Relevé : ça rapproche le DAG des contrats (R, R_z, CZ), le jeu natif vient du backend, des passes possibles avant et après la décomposition, les paires CZ du SAT à lire après la décomposition, et la profondeur du DAG devient propre au backend.
- Sa variante, non tranchée : les optimisations sont des passes sur le DAG. `Compiler` applique les passes universelles sur les portes logiques, puis le backend décompose en natif et applique ses propres passes. Relevé : le backend n'a plus à exposer son jeu natif. Le DAG doit porter portes logiques et natives (paramétrées). Les passes natives sont à écrire comme fonctions sur le DAG, réutilisables par un autre backend du même jeu. Le DAG natif reste invisible hors backend (DOT, profondeur). `apply_opti` : un réglage ou un par couche.
- Décomposition native et optimisation à deux niveaux : description d'issue rédigée, chantier reporté.
- Estimation de ressources, ses choix : `Backend.resource_estimation() -> dict[str, ResourceEstimationResult]` (`utils/estimation.py`, champs `name`, `value`, `unit`, `description`), déléguée par `Compiler`. Profondeur du DAG reportée à l'issue de décomposition native. Restent : atomes, CZ, impulsions `raman`, durée totale. Ouvert : compter dans `translate` ou relire la `Sequence`.
- Implémenté par lui : compteurs `cz_count`/`raman_count` incrémentés pendant la traduction (`raman_count` dans `_rotation`, après le cas θ = 0), `int(get_duration())`, gardes avant `build`. Vérifié contre les impulsions réelles de la `Sequence` sur 33 circuits : aucun écart. Son choix : pas de tests pour l’estimation.
- Suite hésitante : refonte du DAG (décomposition native) ou nouvelle passe. Proposé : d'abord lister sur papier les passes visées et leur niveau (logique/natif), pour en tirer ce que le DAG doit supporter, puis faire la refonte.
- Catalogue de passes présenté. Logiques : annulation d'inverses, annulation par commutation, réécriture de motifs, portes diagonales retirées en début (état |0…0⟩) et en fin (avant mesure en base Z, contrat « tout mesuré à la fin »). Natives : fusion 1 qubit, R_z poussées vers la fin, resynthèse de blocs à 2 qubits (≤ 3 CZ). Backend : impulsions multi-cibles, ordre pour limiter les reciblages. Relevé : le jeu x, y, z, h, cz est Clifford, donc resynthèse Clifford possible tant qu'il n'y a pas de porte non-Clifford.
- Question : élargir le jeu de portes ? Relevé : `reduce_unitary_gate` suppose que toute porte est son propre inverse (même `symbol` → suppression), faux pour S, T ou les rotations paramétrées. Avis donné : élargir avec la refonte du DAG (une porte = une règle de décomposition en natif), pas avant. Alternative : `qiskit.transpile(basis_gates=…)` en amont.
- Textes d'issues rédigés : passes d'optimisation (issue mère, une sous-issue par passe) et élargissement du jeu de portes (après la refonte du DAG). Prochaine séance : refonte du DAG sur papier, en commençant par « qu'est-ce qu'une porte » (une hiérarchie ou deux, paramètres, contrats = portes natives ?).

### 2026-11-15
- Refonte du DAG, sa proposition de cycle de vie : création → optimisation (`Compiler`) → optimisation (backend, portes logiques) → décomposition en natif (backend) → optimisation (backend, natif). Ouvert : critère entre les deux optimisations du backend.
- SAT hors sujet pour l'instant ; exigence retenue : reconnaître les CZ dans le DAG natif.
- Son intuition : des optimisations logiques guidées par le backend. Relevé : souvent une passe générique + un modèle de coût du backend (CZ ≈ 3,7 µs et ≈ 1 % d'erreur, Z virtuelle gratuite sur Pulser), donc l'étape 3 pourrait se fondre dans l'étape 2. Certains motifs (H·CZ·H) se reconnaissent mieux avant la décomposition. Pas tranché.
- Son choix : deux DAG et deux jeux de portes (logique, natif), pas de type `Gate` commun. La décomposition est une fonction DAG logique → nouveau DAG natif. Ouvert : structure du DAG dupliquée ou générique sur le type de nœud ; passes valables aux deux niveaux (annulation d'inverses) écrites deux fois ou via une interface minimale.
- Son choix : DAG générique sur le type de porte (syntaxe 3.12 `DAG[G: …]`). Contraintes vues : borne sur un `Protocol` ou liste fermée de types ; seulement statiques (pyright), une garde à l'exécution demande un `isinstance` et une classe ou un jeu de portes passé au constructeur. Enum « à la Java » (jeu de portes → tuple de classes) possible, rôle à préciser.
- Son choix : portes natives figées par backend (ou famille, ex. atomes neutres), la décomposition devient une fonction de mapping du backend (fin de `Gate.contracts()`). Les contrats `R`/`Rz`/`CZ` deviennent le jeu natif. Relevé : ajouter une porte logique touche chaque backend (inverse de `contracts()`) ; garde statique possible par `match` + `assert_never` sur une union fermée ; mapping en fonction libre partageable sans `ColdAtomsBackend`. Jeu intermédiaire universel : écarté pour l'instant.
- Variante examinée et écartée : une méthode de décomposition par famille de backend dans chaque porte (ou visiteur). Elle fait dépendre la couche logique des jeux natifs, et ajouter une famille touche chaque porte.
- Conséquence : la notion de contrat disparaît (`Gate.contracts()` supprimée). `R`, `Rz`, `CZ` restent comme portes natives, à déplacer de `utils/` vers le backend ou la famille atomes neutres. `translate` parcourt le DAG natif.
- Portes logiques (implémentées par moi à sa demande, `DAG/logical_gate.py`) : enum `LogicalGateKind` (symbol, arity, inverse par nom, is_diagonal) + `@dataclass(frozen=True) LogicalGate(kind, qubits: tuple)`, arité et qubits distincts vérifiés dans `__post_init__`. `symbol` exposé pour le DAG, `from_symbol` pour le convertisseur.
- `Gate.py` supprimé. La borne du DAG est un `Protocol` `Gate` (`symbol`, `qubits`) dans `DAG.py`. `_gate_types` remplacé par `LogicalGateKind`. Reste cassé : `PulserBackend.translate` appelle `gate.contracts()`, en attente de la décomposition dans le backend.
- Sa pipeline : `Compiler` : création du DAG logique → optimisation | backend : optimisation (logique) → conversion en natif → optimisation (native) → SAT.

### 2026-11-16
- Analyse des écarts avec le papier KQD (`ETEQ/papier.pdf`, Yoshioka et al. 2024) : circuits H + CX (préparation contrôlée), Trotter d'ordre 2 en exp(−iθ(XX+YY+ZZ)) sur un heavy-hex 3-coloré (3 CZ par arête), mesures X/Y sur l'ancilla et Pauli sur le reste, jusqu'à 56+1 qubits.
- Ce qui manque : portes paramétrées (`LogicalGate` sans paramètre), CX, RZ/SX/rotations, portes composites (`PauliEvolution`), `barrier` et `measure` (refusés par `from_symbol`), et `translate` en attente de la décomposition native.
- Constaté : `raman_local` et `rydberg_local` ont `max_targets = 1` et un reciblage de 220 ns, donc tout est sérialisé. Une CZ à Ω = 2 dure ≈ 15 µs (3,74 + 7,48 + 3,74). Avec quelques centaines de CZ, on arrive à quelques ms, et l'erreur s'accumule à ≈ 1 % par CZ.
- À 57 qubits : SAT jamais testé à cette taille, émulation QuTiP impossible (3 niveaux par atome), donc ni `run` ni les tests e2e ne s'appliquent.
- Roadmap proposée à sa demande, rien de tranché : décomposition native → portes paramétrées + CX → `barrier`/`measure` → petite instance KQD comparée à Qiskit → instance complète en build seul. Choix ouverts : `transpile` Qiskit en amont ou support des portes composites, sort de `reduce_unitary_gate` avec des angles, taille de la petite instance.
- Son choix : le circuit KQD (`ETEQ/papier.pdf`, arXiv:2407.14431) sert de test concret pour le compilateur, sans reproduire l'algorithme. Une issue mère et 5 sous-issues : portes paramétrées, CX et rotations, `barrier`/`measure`, petite instance comparée à Qiskit, build seul à 57 qubits. #27 est le prérequis.
- Arborescence des backends, son choix : `backend/utils/` (`Backend`, `make_backend`) et un dossier par backend (`backend/pulser/` : `pulser_backend.py`, `pulser_native_gates.py`). La base `NativeGates` est dans `backend/utils/native_gates.py`.
- Portes natives Pulser, son choix : une classe de base `NativeGates` (`qubits`, arité et doublons vérifiés dans `__post_init__`) et des sous-classes dataclass `R`, `Rz`, `CZ` avec leurs paramètres. `symbol` et `arity` passent en `ClassVar` (redéfinir des champs avec une valeur par défaut cassait l'ordre des champs hérités). Relevé : une union fermée `R | Rz | CZ` permet un `match` exhaustif (`assert_never`), une base ouverte non.
- `CZ` symétrique, son choix : les qubits sont triés dans `CZ.__post_init__` (`object.__setattr__`, après la validation de la base), donc `CZ((1, 0)) == CZ((0, 1))`. Le contrôle choisi par `translate` sera toujours le plus petit indice.
- `NativeGates` sorti dans `backend/utils/` comme modèle commun aux backends (son choix ; `LogicalGate` garde sa propre validation). Envisagé, non tranché : mettre la traduction Pulser dans les classes de portes. Pour l'instant, la traduction reste dans le backend (seulement ≈ 20 lignes allégées, les portes auraient besoin de l'état et des primitives du backend). Alternative notée : un module de traduction séparé dans `backend/pulser/`.
- Décomposition logique → natif (`_logical_to_native`) : `match` sur `gate.kind` + `assert_never`, conforme à `pulses.typ`. Traduction natif → impulsions (`_translate_native_gate`) : motifs de tuple (`R((q,), theta, phi)`, `CZ((q0, q1))`) et `TypeError` en dernier cas, son choix. Relevé : un sous-motif de tuple sur `tuple[int, ...]` peut échouer, donc pyright ne réduit pas l'union et `assert_never` est refusé (il passe avec de simples captures).
- Son objectif : alléger `pulser_backend.py` pour n'y garder que des appels. Blocs relevés selon l'état lu/écrit : placement, registre, décomposition (sans état), traduction en impulsions (séquence, canaux, compteurs), exécution, estimation. Ouvert pour la prochaine séance : le backend garde-t-il l'état du résultat, où vont les compteurs, les étapes intermédiaires (DAG natif, positions) sont-elles visibles de l'extérieur. Restent : `build` n'appelle pas la décomposition ni la traduction, `entries` partagé entre les deux DAG, `Backend` importe encore `Contract` et déclare `translate`.

## Temps passé

**Total : ≈ 45,5 h** (au 2026-11-16).

Méthode initiale : union de deux sources, sans compter deux fois les chevauchements.
- Commits de toutes les branches : deux commits à moins de 2 h d'écart sont dans la même séance, qui compte du premier au dernier commit, + 1 h avant le premier.
- Conversations Claude Code (`~/.claude/projects/…/*.jsonl`, horodatées, disponibles depuis le 2026-10-10) : deux messages à moins de 30 min d'écart sont dans la même séance.

Borne basse : le travail sur papier hors commit et hors conversation n'est pas compté.

En fin de séance, j'ajoute une ligne avec la durée de la conversation (même découpage à 30 min) et je mets le total à jour.

| Date | Durée |
|---|---|
| 2026-10-05 | 1,4 h |
| 2026-10-06 | 1,0 h |
| 2026-10-07 | 1,0 h |
| 2026-10-08 | 2,2 h |
| 2026-10-10 | 2,4 h |
| 2026-10-11 | 3,9 h |
| 2026-10-12 | 0,8 h |
| 2026-10-17 | 1,7 h |
| 2026-10-18 | 1,9 h |
| 2026-10-19 | 2,1 h |
| 2026-10-24 | 2,2 h |
| 2026-10-26 | 3,9 h |
| 2026-10-30 | 1,1 h |
| 2026-11-04 | 0,5 h |
| 2026-11-05 | 4,5 h |
| 2026-11-06 | 3,3 h |
| 2026-11-08 | 5,7 h |
| 2026-11-11 | 0,1 h |
| 2026-11-12 | 0,5 h |
| 2026-11-13 | 0,6 h |
| 2026-11-14 | 1,6 h |
| 2026-11-15 | 1,4 h |
| 2026-11-16 | 1,7 h |
