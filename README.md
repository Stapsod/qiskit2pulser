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
QuantumCircuit ─► DAG ─► optimisation ─► placement des atomes (SAT) ─► Sequence Pulser ─► émulation
```

1. **DAG** : une porte par nœud, un successeur par qubit. Portes supportées : `x`, `y`, `z`, `h`, `cz`.
2. **Optimisation** : suppression des paires de portes à 1 qubit identiques et adjacentes sur un même fil (`X X`, `H H`…), y compris en cascade (`X Y Y X` → rien).
3. **Placement** : les atomes sont placés sur une grille dans le disque du device (`DigitalAnalogDevice`). Contraintes : distance minimale entre atomes, et les deux atomes de chaque CZ à portée l'un de l'autre. Le solveur est PySAT (CaDiCaL).
4. **Backend Pulser** : chaque porte se décompose en opérations natives (R(θ, φ), R_z, CZ), traduites en impulsions Blackman (`raman_local` pour les portes à 1 qubit, `rydberg_local` pour la CZ).
5. **Exécution** : émulation QuTiP sur N shots. Le résultat (`CompilerResult`) donne les comptages, avec les bitstrings dans l'ordre de Qiskit (q0 à droite).

## Utilisation

Compile et exécute (1000 shots) le circuit de démo (`demo_circuit()` dans `src/qiskit2pulser/__init__.py`), puis affiche le `CompilerResult`.

```bash
uv run qiskit2pulser                  # compile, émule et affiche les comptages
uv run qiskit2pulser dag.dot          # écrit aussi le DOT du DAG (optimisé) dans out/dag.dot
uv run qiskit2pulser --show           # ouvre aussi le graphe du DAG
uv run qiskit2pulser --help
```

`--show` nécessite [Graphviz](https://graphviz.org/) (commande `dot`) et le visionneur [feh](https://feh.finalrewind.org/).

Depuis Python :

```python
from qiskit2pulser.compiler.compiler import Compiler
from qiskit2pulser.parameters.compiler_parameters import CompilerParameters

compiler = Compiler(CompilerParameters(qc, "config.toml", apply_opti=True))
compiler.build()
result = compiler.run(1000)   # CompilerResult(counts=..., shots=1000, ...)
```

## Configuration

`config.toml` :

| Section | Clé | Rôle |
|---|---|---|
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
│   ├── DAG/             # DAG, portes, conversion Qiskit → DAG, optimisation
│   ├── layout/          # grille de placement et géométrie
│   ├── solvers/         # placement SAT (classe Solver + PySAT, factory)
│   ├── backend/         # classe Backend + PulserBackend, factory
│   ├── parameters/      # paramètres (compiler, layout, solver, backend, pulser)
│   └── utils/           # contrats (opérations natives), CompilerResult
├── formalisations/      # notes Typst
└── tests/
    ├── testsuite.py     # point d'entrée de `uv run testsuite`
    ├── DAG/ layout/ solvers/ backend/
    └── end2end/         # comparaison Pulser ↔ Qiskit
```

## État d'avancement

- [x] Mise en place de l'environnement et de la suite de tests
- [x] Conversion d'un circuit Qiskit en DAG (portes `x`, `y`, `z`, `h`, `cz`), avec export DOT et affichage via Graphviz
- [x] Placement des atomes par SAT
- [x] Conversion des portes en impulsions
- [x] Tests fonctionnels de bout en bout contre Qiskit
- [x] Première passe d'optimisation : suppression des portes à 1 qubit identiques adjacentes
- [ ] Passes d'optimisation supplémentaires
- [ ] Placement derrière le backend (modularité)
- [ ] Mode analogique
