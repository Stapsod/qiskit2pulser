# qiskit2pulser

Compilateur de circuits quantiques [Qiskit](https://www.ibm.com/quantum/qiskit) vers des séquences d'impulsions [Pulser](https://github.com/pasqal-io/Pulser) pour processeurs à atomes neutres.

## Principe

Qiskit décrit un circuit en **portes logiques** ; Pulser décrit une **séquence d'impulsions laser** appliquées à des atomes disposés dans un `Register`. Le compilateur fait le pont.

## Installation

Nécessite [uv](https://docs.astral.sh/uv/) et Python ≥ 3.12.

```bash
git clone <url-du-repo>
cd qiskit2pulser
uv sync
```

## Pipeline

```
QuantumCircuit ─► DAG logique ─► optimisation ─► [backend Pulser : DAG natif ─► placement des atomes (SAT) ─► Sequence] ─► émulation
```

`Compiler` ne connaît que les étapes génériques (DAG logique, optimisation). Le jeu de portes natif, le placement et les impulsions sont propres aux atomes neutres : `PulserBackend.build` ne fait qu'enchaîner trois classes de `backend/pulser/` (`PulserTranspiler`, `PulserRegisterBuilder`, `PulserSequenceBuilder`).

1. **DAG logique** : une porte par nœud, un successeur par qubit. Le DAG est générique sur le type de porte (protocole `Gate` : `symbol`, `qubits`). Portes logiques supportées : `x`, `y`, `z`, `h`, `cz`.
2. **Optimisation** : suppression des paires de portes à 1 qubit identiques et adjacentes sur un même fil (`X X`, `H H`…), y compris en cascade (`X Y Y X` → rien). Activée par `apply_opti` dans `[compiler]`.
3. **DAG natif** (`PulserTranspiler`) : chaque porte logique est décomposée en portes natives Pulser, R(θ, φ), R_z(φ) et CZ, dans un nouveau DAG.
4. **Placement** (`PulserRegisterBuilder`) : les atomes sont placés sur une grille dans le disque du device (`DigitalAnalogDevice`). Contraintes : distance minimale entre atomes, et les deux atomes de chaque CZ à portée l'un de l'autre. Les paires de CZ sont lues dans le DAG natif. Le solveur est PySAT (CaDiCaL).
5. **Impulsions** (`PulserSequenceBuilder`) : chaque porte native est traduite en impulsions Blackman (`raman_local` pour R, `rydberg_local` pour la CZ) ; R_z est un `phase_shift` virtuel.
6. **Exécution** : émulation QuTiP sur N shots. Le résultat (`CompilerResult`) donne les comptages, avec les bitstrings dans l'ordre de Qiskit (q0 à droite).

## Utilisation

Compile et exécute (1000 shots) le circuit de démo (`demo_circuit()` dans `src/qiskit2pulser/__init__.py`), puis affiche le `CompilerResult`.

```bash
uv run qiskit2pulser config.toml                     # compile, émule et affiche les comptages
uv run qiskit2pulser config.toml --dotfile dag.dot   # écrit aussi le DOT du DAG (optimisé) dans out/dag.dot
uv run qiskit2pulser config.toml --show              # ouvre aussi le graphe du DAG
uv run qiskit2pulser --help
```

Le chemin de la config est obligatoire.

`--show` nécessite [Graphviz](https://graphviz.org/) (commande `dot`) et le visionneur [feh](https://feh.finalrewind.org/).

Depuis Python :

```python
import tomllib

from qiskit2pulser.compiler.compiler import Compiler
from qiskit2pulser.parameters.compiler_parameters import CompilerParameters

with open("config.toml", "rb") as f:
    config = tomllib.load(f)
compiler = Compiler(CompilerParameters(qc, config))
compiler.build()
result = compiler.run(1000)  # CompilerResult(counts=..., shots=1000, ...)
```

### Estimation de ressources

Après `build`, sans émulation (donc aussi pour des circuits trop gros pour l'émulateur) :

```python
estimates = compiler.resource_estimation()  # dict nom → ResourceEstimationResult
estimates["CZ_count"].value
```

Chaque estimation porte un nom, une valeur, une unité et une description. Chaque backend renvoie toutes les métriques qu'il calcule à peu de frais. Pour Pulser :

| Nom | Unité | Mesure |
|---|---|---|
| `qubits_count` | atomes | nombre d'atomes du registre |
| `CZ_count` | portes | nombre de CZ (3 impulsions `rydberg_local` chacune) |
| `raman_count` | impulsions | nombre d'impulsions `raman_local` (les R_z, virtuelles, ne comptent pas) |
| `duration` | ns | durée totale de la `Sequence` |

Les nombres de CZ et d'impulsions raman sont comptés sur le DAG natif (une porte native donne une instruction).

## Configuration

Le fichier est lu une seule fois (dans `main`), et le dict descend jusqu'au backend : `Compiler` ne lit que `[compiler]` et `[backend]`, et chaque backend prend ses propres sections (`[pulser]` et `[SAT_solver]` pour Pulser).

`config.toml` :

| Section | Clé | Rôle |
|---|---|---|
| `[compiler]` | `apply_opti` | active la passe d'optimisation (`true`/`false`) |
| `[backend]` | `type` | backend de sortie (`pulser`) |
| `[pulser]` | `omega` | pic de Rabi des impulsions CZ (rad/µs), fixe le rayon de blocage R_b |
| | `omega_raman` | pic de Rabi des portes à 1 qubit (optionnel, `max_amp` de `raman_local` par défaut) |
| | `step` | pas de la grille de placement (µm) |
| | `threshold` | distance max entre les atomes d'une CZ (µm), ≤ R_b(omega), R_b par défaut |
| `[SAT_solver]` | `type`, `name` | sous-classe de solveur (`pysat`) et solveur PySAT (`cadical195`) |

L'erreur d'une CZ croît vite avec la distance (≈ 0,57·(d/R_b)⁶) : `threshold = 6.0` à `omega = 2.0` donne ≈ 1 % d'erreur par CZ.

## Tests

```bash
uv run testsuite              # lance toute la suite
uv run testsuite -k cz -v     # les arguments sont transmis à pytest
uv run testsuite --ignore tests/end2end   # sans les tests d'émulation (les plus lents)
```

Les tests de bout en bout (`tests/end2end/`) comparent les distributions émulées par Pulser à celles de Qiskit, puis les résultats avec et sans optimisation. La tolérance couvre le bruit d'échantillonnage et l'erreur des CZ.

Les tests n'utilisent pas `config.toml` : leur config est écrite en dur dans `tests/config.py` (`make_config()`), car la tolérance des tests de bout en bout dépend de son `threshold` (6 µm).

## Notes de formalisation

Les notes (Typst) sont dans `formalisations/` et se compilent avec [just](https://github.com/casey/just) et [Typst](https://typst.app/). Les PDF sont écrits dans `formalisations/out/`.

```bash
cd formalisations
just conventions       # conventions Qiskit ↔ Pulser mesurées dans l'émulateur
just SAT_clauses       # encodage SAT du placement des atomes
just SAT_alternatives  # alternatives au SAT (MaxSAT, ILP/CP-SAT, heuristiques)
just pulses            # portes → impulsions (Ω, forme, durée)
just all               # tous les documents
```

## Structure

```
.
├── config.toml
├── src/qiskit2pulser/
│   ├── __init__.py      # main et circuit de démo
│   ├── compiler/        # Compiler : enchaîne les étapes
│   ├── DAG/             # DAG générique, portes logiques, conversion Qiskit → DAG, optimisation
│   ├── layout/          # grille de placement et géométrie
│   ├── solvers/         # placement SAT (classe Solver + PySAT, factory)
│   ├── backend/
│   │   ├── utils/       # classe Backend, factory, base NativeGates des portes natives
│   │   └── pulser/      # PulserBackend, portes natives, transpiler, register et sequence builders
│   ├── parameters/      # paramètres (compiler, layout, solver, backend, pulser)
│   └── utils/           # CompilerResult, estimations
├── formalisations/      # notes Typst
└── tests/
    ├── testsuite.py     # point d'entrée de `uv run testsuite`
    ├── config.py        # config des tests (dict en dur)
    ├── DAG/ layout/ solvers/ backend/
    └── end2end/         # comparaison Pulser ↔ Qiskit
```

## État d'avancement

- [x] Mise en place de l'environnement et de la suite de tests
- [x] Conversion d'un circuit Qiskit en DAG (portes `x`, `y`, `z`, `h`, `cz`), avec export DOT et affichage via Graphviz
- [x] Placement des atomes par SAT
- [x] Conversion des portes en impulsions
- [x] DAG à deux niveaux : portes logiques, puis portes natives propres au backend
- [x] Tests fonctionnels de bout en bout contre Qiskit
- [x] Première passe d'optimisation : suppression des portes à 1 qubit identiques adjacentes
- [x] Estimation de ressources (atomes, CZ, impulsions, durée)
- [ ] Passes d'optimisation supplémentaires
- [x] Placement derrière le backend (modularité)
- [x] Config lue une seule fois
- [ ] Mode analogique
