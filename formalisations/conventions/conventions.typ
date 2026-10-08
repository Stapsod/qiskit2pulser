#import "/template_article/lib.typ": *

#show: article.with(
  title: "Conventions Qiskit ↔ Pulser",
  authors: (
    (name: "Ugo Col", affiliation: "EPITA - Quantum"),
  ),
  abstract: [
    Ce document fixe les conventions, mesurées dans l'émulateur, utilisées par
    le compilateur Qiskit → Pulser (`DigitalAnalogDevice`, canal
    `raman_local`, base `"digital"`, Pulser 1.9.1). Les §n renvoient aux
    sections du notebook `notebooks/pulser_tests.ipynb`.
  ],
  keywords: ("Qiskit", "Pulser"),
)

= Conventions mesurées

#single_column_table(
  headers: ([Question], [Réponse], [Preuve (mesure dans l'émulateur)]),
  content: (
    [Correspondance des états],
    [$ket(0)_"Qiskit" = ket(g)$, \ $ket(1)_"Qiskit" = ket(h)$],
    [§1. Impulsion $pi$ : statevector $[0, 1]$, bitstring `'1'`. \
      Impulsion $2 pi$ : statevector $[1, 0]$, bitstring `'0'`.],
    [Aire → angle],
    [Une aire $theta$ donne une rotation d'angle $theta$ (aucun facteur).],
    [§2. Pour $theta in {pi\/4, pi\/2, 2pi\/3, pi, 3pi\/2}$, $P(1)$ mesurée
      $= sin^2(theta\/2)$ (0.146, 0.5, 0.75, 1, 0.5).],
    [Impulsion de phase $0$],
    [$R_x (+theta)$],
    [§3. Aire $pi\/2$ : $[0.707, -0.707 i] tilde.eq R_x (+pi\/2) ket(0)$],
    [Impulsion de phase $pi\/2$],
    [$R_y (-theta)$ (sens inversé)],
    [§3. Aire $pi\/2$ : $[0.707, -0.707] tilde.eq R_y (-pi\/2) ket(0)$],
    [Axe de rotation d'une impulsion de phase $phi$],
    [$(cos phi, -sin phi, 0)$, alors que Qiskit $R(theta, phi)$ tourne autour
      de $(cos phi, +sin phi, 0)$],
    [Déduit des lignes « phase $0$ » et « phase $pi\/2$ ».],
    [`phase_shift(φ)` équivaut-il à $R_z (phi)$ ou $R_z (-phi)$ ?],
    [$R_z (+phi)$, à un $R_z$ final près sur le statevector (virtual Z : seules
      les impulsions suivantes sont déphasées)],
    [§4. Impulsion $pi\/2$ (phase $0$), `phase_shift(π/2)`, impulsion $pi\/2$
      (phase $pi\/2$) : populations $[1, 0]$. Qiskit
      $R_y (-pi\/2) R_z (+pi\/2) R_x (pi\/2)$ donne $[1, 0]$, avec
      $R_z (-pi\/2)$ on obtient $[0, 1]$.],
    [Ordre des bits dans les bitstrings Pulser vs Qiskit (little-endian) ?],
    [Inversé : Pulser est big-endian, `q0` est le bit le plus à *gauche*
      (bitstrings et indice du statevector). Il faut retourner les
      bitstrings.],
    [§5. Impulsion $pi$ sur `q0` seul : Pulser `'10'`, statevector
      $e_2$. Qiskit `x(0)` : `'01'`, statevector $e_1$. Symétrique pour
      `q1`.],
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
  d'aire $theta$ et de phase $-phi$. \
  La porte Qiskit $R_z (phi)$ se traduit par `phase_shift(φ)` (aucune
  impulsion). Les statevectors Pulser et Qiskit ne coïncident alors qu'à un
  $R_z$ final près : comparer les populations, ou corriger le référentiel. \
  Les bitstrings Pulser se lisent à l'envers de Qiskit : retourner la chaîne
  (et permuter le statevector) avant de comparer.
]
