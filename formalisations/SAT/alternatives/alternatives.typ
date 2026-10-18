#import "/template_article/lib.typ": *

#show: article.with(
  title: "Alternatives au SAT pour le placement",
  authors: (
    (name: "Ugo Col", affiliation: "EPITA - Quantum"),
  ),
  abstract: [
    Note de côté, au cas où l'approche SAT (voir `SAT/clauses`) se révèle
    peu intéressante. Elle recense les autres pistes envisagées le
    2026-10-18 pour placer les qubits sur le `DigitalAnalogDevice`, avec
    leurs avantages et leurs limites. Rien n'est tranché : le SAT reste la
    piste suivie.
  ],
  keywords: ("Pulser", "SAT", "placement"),
)

= Pourquoi chercher ailleurs

Le SAT répond à une question exacte : existe-t-il, sur la grille, un
placement valide pour Pulser où toutes les paires CZ sont voisines ? Ses
limites :
- *Tout ou rien.* Un UNSAT ne dit pas quelles paires bloquent. Or l'UNSAT
  risque d'être fréquent dès qu'un circuit a un peu de CZ, et c'est
  justement là que le routage a besoin d'information.
- *Pas de notion de qualité.* Toutes les distances de la couronne se valent,
  y compris celles proches de $R_b$, où le blocage est imparfait.
- *Coût des UNSAT.* Le solveur doit réfuter chaque placement partiel sous
  toutes ses symétries de grille.

Le fond du problème est NP-difficile : décider si un graphe d'interactions
se dessine avec « arête $<=>$ distance $<=$ seuil » est difficile. Toute
méthode exacte est exponentielle dans le pire cas.

= Pistes

#single_column_table(
  headers: ([Piste], [Pour], [Contre]),
  content: (
    [*SAT* (piste actuelle)],
    [Exact sur la grille : trouve un placement s'il existe, prouve l'UNSAT
      sinon. Formalisme prêt et démontré.],
    [Tout ou rien, pas d'objectif de qualité, UNSAT coûteux.],
    [*MaxSAT* : familles 1 à 4 dures, couronnes CZ souples],
    [Réutilise tout le formalisme. Maximise le nombre de paires CZ voisines
      et dit lesquelles ne le sont pas, ce dont le routage a besoin.],
    [Optimisation plus dure qu'une décision. Solveurs en général plus lents
      que le SAT pur.],
    [*ILP / CP-SAT*],
    [Mêmes variables $x$, avec un objectif possible (éloigner les paires du
      seuil, compacité, ...). Cardinalités natives, sans compteur de Sinz.],
    [Changement d'outil et de formalisme. Pas forcément plus rapide à cette
      taille.],
    [*Heuristiques* : glouton, disposition par ressorts dans le plan
      continu, puis correction de la distance minimale],
    [Très rapide, passe à 100 qubits, pas de grille.],
    [Aucune garantie : un échec ne prouve rien. La validité Pulser est à
      vérifier après coup.],
  ),
  false,
  none,
)

La littérature sur la compilation pour atomes neutres utilise les deux
familles : méthodes exactes à base de solveurs (SMT, par exemple les travaux
de type OLSQ) et heuristiques.

= Bilan au 2026-10-18

- Il n'y a pas de piste meilleure dans l'absolu : tout dépend de la priorité
  (exactitude, information pour le routage, ou vitesse sur de gros
  circuits).
- MaxSAT est la piste qui répond au tout-ou-rien en gardant le plus du
  travail fait.
- Les familles 1 à 4 (un emplacement par qubit, un qubit par emplacement,
  distance minimale) servent quelle que soit la piste exacte retenue :
  passer du SAT à MaxSAT plus tard ne les change pas.
