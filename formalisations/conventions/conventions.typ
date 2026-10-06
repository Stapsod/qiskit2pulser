#import "/template_article/lib.typ": *

#show: article.with(
  title: "Conventions Qiskit ↔ Pulser",
  authors: (
    (name: "Ugo Col", affiliation: "EPITA - Quantum"),
  ),
  abstract: [
    Ce document fixe les conventions, mesurées dans l'émulateur, utilisées par
    le compilateur Qiskit → Pulser (`DigitalAnalogDevice`, canal
    `raman_local`, base `"digital"`, Pulser 1.9.1).
  ],
  keywords: ("Qiskit", "Pulser"),
)

#let todo = text(fill: red.darken(20%), style: "italic")[À mesurer]

= Conventions mesurées

#single_column_table(
  headers: ([Question], [Réponse], [Preuve (mesure dans l'émulateur)]),
  content: (
    [Correspondance des états],
    [$ket(0)_"Qiskit" = ket(g)$, \ $ket(1)_"Qiskit" = ket(h)$],
    [Sans impulsion : statevector $[1, 0]$, bitstring `'0'`. \
      Après une impulsion $pi$ : statevector $[0, 1]$, bitstring `'1'`.],

    [Aire → angle],
    [Une aire $theta$ donne une rotation d'angle $theta$ (aucun facteur).],
    [],

    [Impulsion de phase $0$],
    [$R_x (+theta)$],
    [Aire $pi\/2$ : $[0.707 i, 0.707] = i dot R_x (+pi\/2) ket(0)$],

    [Impulsion de phase $pi\/2$],
    [$R_y (-theta)$ (sens inversé)],
    [Aire $pi\/2$ : $[-0.707, 0.707] = -1 dot R_y (-pi\/2) ket(0)$],

    [Axe de rotation d'une impulsion de phase $phi$],
    [$(cos phi, -sin phi, 0)$, alors que Qiskit $R(theta, phi)$ tourne autour
      de $(cos phi, +sin phi, 0)$],
    [Déduit des lignes « phase $0$ » et « phase $pi\/2$ ».],

    [`phase_shift(φ)` équivaut-il à $R_z (phi)$ ou $R_z (-phi)$ ?],
    todo,
    todo,

    [Ordre des bits dans les bitstrings Pulser vs Qiskit (little-endian) ?],
    todo,
    todo,
  ),
  false,
  none,
)

#block(
  width: 100%,
  inset: 10pt,
  radius: 4pt,
  stroke: blue.darken(20%),
  fill: blue.lighten(90%),
)[
  *Règle de lowering* \
  La porte Qiskit $R(theta, phi)$ se traduit par une impulsion `raman_local`
  d'aire $theta$ et de phase $-phi$.
]
