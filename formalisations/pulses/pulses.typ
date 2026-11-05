#import "/template_article/lib.typ": *

#show: article.with(
  title: "Portes → impulsions Pulser",
  authors: (
    (name: "Ugo Col", affiliation: "EPITA - Quantum"),
  ),
  abstract: [
    Ce document fixe la traduction des portes du DAG en impulsions Pulser
    (`DigitalAnalogDevice`, Pulser 1.9.1) et les choix qui la
    sous-tendent : rôle des deux $Omega$, forme et durée des impulsions,
    contraintes du device. État au 2026-11-05. Il s'appuie sur
    `conventions.typ`.
  ],
  keywords: ("Pulser", "portes", "impulsions"),
)

= Rappels des conventions

- $ket(0)_"Qiskit" = ket(g)$, $ket(1)_"Qiskit" = ket(h)$.
- La porte Qiskit $R(theta, phi)$ devient une impulsion `raman_local`
  d'aire $theta$, de phase $-phi$ et de désaccord nul.
- $R_z (phi)$ devient `phase_shift(φ)` (Z virtuel) : aucune impulsion, les
  impulsions suivantes du qubit sont déphasées. Les populations sont exactes,
  le statevector diffère d'un $R_z$ final.
- Une impulsion résonante de phase constante est une rotation d'angle
  $theta = integral Omega(t) dif t$ (l'aire), autour de l'axe
  $(cos phi, -sin phi, 0)$. Seule l'aire compte, pas la forme.

= Canaux et contraintes du device

#single_column_table(
  headers: ([Canal], [Transition], [Rôle]),
  content: (
    [`raman_local`], [$g <-> h$ (base `digital`)], [portes à 1 qubit],
    [`rydberg_local`], [$g <-> r$ (base `ground-rydberg`)], [CZ],
    [`rydberg_global`], [$g <-> r$, tous les atomes], [mode analogique (plus tard)],
  ),
  false,
  none,
)

- Canaux locaux : `max_targets = 1`, retarget de 220 ns. Toutes les portes
  locales sont donc sérialisées sur leur canal, pas seulement les CZ.
- Durées : entières en ns, multiples de 4 (`clock_period`), au moins 16
  (`min_duration`).
- `max_amp` $= 2 pi dot 10$ rad/µs sur `raman_local` et `rydberg_local`.

= Choix : deux $Omega$, qui désignent le pic

#single_column_table(
  headers: ([Paramètre], [Canal], [Rôle], [Valeur]),
  content: (
    [`omega`], [`rydberg_local`], [vitesse de la CZ et $R_b (Omega)$, donc
      le seuil SAT], [config, obligatoire],
    [`omega_raman`], [`raman_local`], [vitesse seulement], [config,
      optionnel, par défaut le `max_amp` du canal],
  ),
  false,
  none,
)

$Omega$ désigne le *pic* d'amplitude, car les deux limites physiques
(`max_amp` et le blocage) portent sur le pic. `PulserParameters` vérifie
$0 < Omega <= "max_amp"$ pour chacun des deux.

= Choix : forme et durée

- Forme : Blackman partout (spectre plus étroit qu'un créneau). Le pic vaut
  $approx 2.4 times$ l'amplitude moyenne.
- Durée (`PulserBackend._duration`) : la plus courte durée telle que le pic
  reste $<= Omega$ (`BlackmanWaveform.from_max_val(Ω, θ)`), arrondie au
  multiple supérieur de `clock_period`, avec au moins `min_duration`.
  Allonger une impulsion d'aire fixe baisse son pic, donc $Omega$ reste
  respecté. `BlackmanWaveform(durée, θ)` garantit l'aire exacte.

#single_column_table(
  headers: ([Canal], [Aire], [Durée], [Pic / $Omega$]),
  content: (
    [raman], [$pi$], [124 ns], [60.8 / 62.8],
    [raman], [$pi\/2$], [64 ns], [59.3 / 62.8],
    [rydberg ($Omega = 2$)], [$pi$], [3744 ns], [1.998 / 2],
    [rydberg ($Omega = 2$)], [$2 pi$], [7484 ns], [1.999 / 2],
  ),
  false,
  none,
)

= Table de traduction des portes

#single_column_table(
  headers: ([Porte], [Instructions (dans l'ordre)], [Vérification]),
  content: (
    [X], [`raman_local`, aire $pi$, phase $0$], [erreur $< 10^(-5)$],
    [Y], [`raman_local`, aire $pi$, phase $-pi\/2$], [erreur $< 10^(-5)$],
    [Z], [`phase_shift(π)`], [erreur $< 10^(-5)$],
    [H], [`phase_shift(π)`, puis `raman_local`, aire $pi\/2$, phase
      $-pi\/2$], [erreur $< 10^(-5)$],
    [CZ(c, t)], [`rydberg_local` sur c, aire $pi$ ; `rydberg_local` sur t,
      aire $2 pi$ ; `rydberg_local` sur c, aire $pi$], [dépend de $d$, voir
      plus bas],
  ),
  false,
  none,
)

Vérification : émulateur `QutipEmulator`, comparaison des populations avec
Qiskit, avec des sondes $R_x (pi\/2)$ et $R_y (pi\/2)$ avant et après la porte
(9 combinaisons par porte, sur les deux qubits pour la CZ).

= Résultat : la CZ n'est pas fiable au seuil

Erreur maximale de population de la CZ en fonction de la distance $d$ entre
les deux atomes, à $Omega = 2$ rad/µs ($R_b approx 11.8$ µm) :

#single_column_table(
  headers: ([$d$ (µm)], [4], [6], [8], [10], [11.8]),
  content: (
    [erreur], [$8.6 dot 10^(-4)$], [$9.8 dot 10^(-3)$], [$5.5 dot 10^(-2)$],
    [$0.20$], [$0.43$],
  ),
  false,
  none,
)

$R_b$ est la distance où l'interaction vaut $Omega$ : le blocage n'y est pas
assuré, il faut une interaction $>> Omega$. Le seuil par défaut
`threshold` $= R_b (Omega)$ produit donc des CZ fausses. *Ouvert* : choisir
un seuil (ou une marge) selon l'erreur tolérée.

= Architecture

- `PulserBackend` (`backend/pulser_backend.py`) : construit les identifiants
  `q{i}` (dict indice → identifiant, source de vérité), le `Register` (sans
  recentrage) et la `Sequence`. Il porte la création des impulsions et le
  choix de $Omega$ par canal.
- `Gate` ne dépend pas de Pulser.
- *Ouvert* : le contrat. Chaque porte renvoie une liste ordonnée
  d'instructions abstraites (impulsion : canal, qubit, aire, phase ;
  `phase_shift` : qubit, $phi$), que le backend exécute. Restent à définir
  le vocabulaire et la façon de nommer un canal sans Pulser.
