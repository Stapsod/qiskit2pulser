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

## Tests

```bash
uv run testsuite              # lance toute la suite
uv run testsuite -k cz -v     # les arguments sont transmis à pytest
```

## Structure

```
.
├── src/qiskit2pulser/   # le compilateur
└── tests/
    ├── testsuite.py     # point d'entrée de `uv run testsuite`
    └── test_*.py        # les tests
```

## Feuille de route

- [x] Mise en place de l'environnement et de la suite de tests
- [ ] Prise en main de Pulser : porte X par impulsion Raman sur un atome
- [ ] Portes à 1 qubit (`rx`, `ry`, `rz`) vérifiées contre Qiskit
- [ ] Porte CZ par blocage Rydberg
- [ ] Frontend Qiskit : transpilation vers la base native et parcours du DAG
- [ ] Placement des atomes
- [ ] Routage (insertion de SWAP)
- [ ] Optimisations (fusion de rotations, parallélisation)
- [ ] Mode analogique (ex. MIS / QAOA sur l'hamiltonien Rydberg)
