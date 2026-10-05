# qiskit2pulser

Compilateur de circuits quantiques [Qiskit](https://www.ibm.com/quantum/qiskit) vers des séquences d'impulsions [Pulser](https://github.com/pasqal-io/Pulser) pour processeurs à atomes neutres.

> 🚧 Projet personnel en cours de développement — rien n'est encore fonctionnel.

## Principe

Qiskit décrit un circuit en **portes logiques** ; Pulser décrit une **séquence d'impulsions laser** appliquées à des atomes disposés dans un `Register`. Le compilateur fait le pont :

```
QuantumCircuit (Qiskit)
   │ 1. transpile vers une base native : {rz, rx/ry, cz}
   ▼
Circuit natif
   │ 2. placement : qubit → position d'atome (contrainte du rayon de blocage Rydberg)
   │ 3. routage : insertion de SWAP si deux qubits d'une CZ sont trop éloignés
   ▼
   │ 4. génération d'impulsions :
   │    - rz      → phase shift virtuel (aucune impulsion)
   │    - rx/ry   → impulsion Raman locale (aire θ, phase φ)
   │    - cz      → séquence Rydberg π – 2π – π (blocage)
   ▼
pulser.Sequence  ──► 5. vérification : QutipEmulator vs Statevector Qiskit
```

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
