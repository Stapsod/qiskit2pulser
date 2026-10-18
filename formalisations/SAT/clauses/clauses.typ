#import "/template_article/lib.typ": *

#show: article.with(
  title: "Placement des atomes par SAT",
  authors: (
    (name: "Ugo Col", affiliation: "EPITA - Quantum"),
  ),
  abstract: [
    Ce document formalise l'encodage SAT utilisé pour placer les qubits d'un
    circuit sur le `DigitalAnalogDevice` : hypothèses, variables, familles
    de clauses et nombre de clauses. Il fixe l'état des
    décisions au 2026-10-18. Rien n'est encore implémenté.
  ],
  keywords: ("Pulser", "SAT", "placement"),
)

= Hypothèses

- *Device* : `DigitalAnalogDevice`, en 2D, au plus 100 atomes, dans un disque
  de rayon 50 µm, avec une distance minimale de 4 µm entre deux atomes.
  $R_b approx 6.6$ µm à $Omega$ max ($approx 13.3$ µm à
  $Omega = 1$ rad/µs).
- *CZ sérialisées* : deux CZ ne sont jamais exécutées en même temps. Il n'y
  a donc pas de contrainte d'éloignement entre paires CZ. C'est un invariant
  que la construction de la `Sequence` devra respecter.
- *$R_b$ fixé* : le seuil de la couronne CZ (voir la famille 5) est un
  paramètre ajustable, qui doit rester cohérent avec $Omega$.

= Notations

#definition(title: "Instance")[
  - $n$ qubits, indexés $q in {0, ..., n-1}$.
  - $P$ emplacements candidats, indexés $p in {0, ..., P-1}$ : les points
    d'une grille régulière de pas $< 4$ µm compris dans le disque. Avec un
    pas de 2 µm, $P = 1961$.
  - $d(p, p')$ : la distance euclidienne entre deux emplacements.
  - $C$ : l'ensemble des paires CZ dédupliquées, chacune orientée une seule
    fois (convention arbitraire), $m = |C|$.
  - $N(p) = {p' : 4 "µm" <= d(p, p') <= "seuil"}$ : la couronne CZ autour
    de $p$.
  - $D = {{p, p'} : p != p', d(p, p') < 4 "µm"}$ : les couples non ordonnés
    trop proches.
]

= Variables

#single_column_table(
  headers: ([Variable], [Sens], [Nombre]),
  content: (
    [$x_(q,p)$],
    [Le qubit $q$ est sur l'emplacement $p$.],
    [$n P$],
    [$s_(q,k)$, $k in {0, ..., P-2}$],
    [Le qubit $q$ est sur l'un des emplacements $0, ..., k$.],
    [$n (P-1)$],
    [$t_(p,j)$, $j in {0, ..., n-1}$],
    [L'emplacement $p$ porte l'un des qubits $0, ..., j$. En particulier,
      $t_(p,n-1)$ signifie « $p$ est occupé ».],
    [$n P$],
  ),
  false,
  none,
)

Les variables $s$ et $t$ sont auxiliaires. Elles ne sont contraintes que dans
un sens (la variable est vraie *au moins* quand son sens l'exige). La
justification est donnée en @sens-unique.

= Clauses

== Au moins un emplacement par qubit

Pour chaque $q$ :
$ x_(q,0) or x_(q,1) or dots or x_(q,P-1) $

== Au plus un emplacement par qubit

Compteur séquentiel (Sinz, 2005) sur la ligne $q$ de $x$ :
$
  & not x_(q,k) or s_(q,k)       & quad & k = 0, ..., P-2 \
  & not s_(q,k-1) or s_(q,k)     & quad & k = 1, ..., P-2 \
  & not s_(q,k-1) or not x_(q,k) & quad & k = 1, ..., P-1
$
La dernière ligne interdit un deuxième emplacement : si $q$ est déjà placé
avant $k$, il ne peut pas être sur $k$.

== Au plus un qubit par emplacement, et occupation

Le même compteur sur la colonne $p$ de $x$, prolongé d'un cran pour que
$t_(p,n-1)$ couvre tous les qubits :
$
  & not x_(j,p) or t_(p,j)       & quad & j = 0, ..., n-1 \
  & not t_(p,j-1) or t_(p,j)     & quad & j = 1, ..., n-1 \
  & not t_(p,j-1) or not x_(j,p) & quad & j = 1, ..., n-1
$

#remark[
  *Pourquoi il n'y a plus de variable $o_p$ ni de clauses de liaison.* La
  première version utilisait $o_p$ = « $p$ occupé » et $n P$ clauses
  $not x_(q,p) or o_p$. Avec la colonne $t_(p,n-1)$, la chaîne
  $x_(q,p) => t_(p,q) => dots => t_(p,n-1)$ impose déjà la liaison. Il ne
  faut pas s'arrêter à $t_(p,n-2)$ : dans le compteur standard, le dernier
  qubit est seulement testé, il n'allume aucune variable, et il échapperait
  à la distance minimale.
]

== Distance minimale

Pour chaque ${p, p'} in D$, compté une seule fois :
$ not t_(p,n-1) or not t_(p',n-1) $

#remark[
  Il faut exclure $p' = p$ : la clause $not t_(p,n-1) or not t_(p,n-1)$
  interdirait tout emplacement. Le cas de deux qubits sur le même
  emplacement est traité par la famille 3, pas par celle-ci.
]

== Couronne CZ

Pour chaque $(a, b) in C$ et chaque $p$ :
$ not x_(a,p) or or.big_(p' in N(p)) x_(b,p') $
Si $N(p) = emptyset$, la clause se réduit à $not x_(a,p)$. Une seule
direction suffit, car la couronne est symétrique.

= Pourquoi un seul sens suffit <sens-unique>

Les clauses imposent $x_(q,k) => s_(q,k)$ et $s_(q,k-1) => s_(q,k)$, mais
pas la réciproque $s_(q,k) => s_(q,k-1) or x_(q,k)$. Le solveur peut donc
mettre $s_(q,k)$ à vrai sans que $q$ soit placé sur l'un des emplacements
$0, ..., k$. Il en va de même pour $t$. Cela ne change pas la réponse du
solveur.

#theorem(title: "Équisatisfiabilité")[
  Soit $F$ l'ensemble des clauses des familles 1 à 5.
  + Dans tout modèle de $F$, les variables $x$ décrivent un placement valide.
  + Tout placement valide se prolonge en un modèle de $F$.
]

#proof[
  *1. Pas de faux SAT.* On prend un modèle de $F$.
  - Si $x_(q,i)$ et $x_(q,j)$ sont vrais avec $i < j$, alors $s_(q,i)$ est
    vrai, puis $s_(q,j-1)$ par la chaîne, et la clause
    $not s_(q,j-1) or not x_(q,j)$ est violée.
  - Si $x_(i,p)$ et $x_(j,p)$ sont vrais avec $i < j$, le même raisonnement
    sur la colonne $p$ viole $not t_(p,j-1) or not x_(j,p)$.
  - Si deux emplacements ${p, p'} in D$ sont occupés, la chaîne force
    $t_(p,n-1)$ et $t_(p',n-1)$ à vrai, et la clause de distance est violée.
  - Les familles 1 et 5 ne portent que sur $x$ : elles valent directement
    pour le placement.

  L'argument n'utilise que les implications présentes : il suffit que $s$
  et $t$ soient vraies quand $x$ l'impose, jamais qu'elles soient fausses.

  *2. Pas de faux UNSAT.* On part d'un placement valide et on donne aux
  auxiliaires leur valeur « honnête » :
  $
    s_(q,k) = or.big_(k' <= k) x_(q,k') quad quad
    t_(p,j) = or.big_(j' <= j) x_(j',p)
  $
  Les implications sont vraies par construction. La clause
  $not s_(q,k-1) or not x_(q,k)$ dit que $q$ n'est pas à la fois avant $k$
  et sur $k$ : c'est le cas, car $q$ n'a qu'un emplacement. Même chose pour
  $t$. Comme $t_(p,n-1)$ vaut exactement « $p$ est occupé », la distance
  minimale du placement donne la famille 4. Les familles 1 et 5 sont vraies
  par hypothèse.
]

#remark[
  *Ce qui rend l'argument possible.* En dehors de leur propre chaîne, $s$ et
  $t$ n'apparaissent qu'en négatif ($not s or not x$, $not t or not x$,
  $not t or not t$). Une auxiliaire mise à vrai à tort ne peut donc
  qu'interdire des placements, jamais en autoriser. Deux conséquences :
  - Un modèle peut contenir des valeurs de $s$ ou $t$ qui ne correspondent à
    rien. Le placement se lit sur $x$ seul.
  - Si une clause utilisait un jour $t$ en positif, par exemple
    $not x_(a,p) or or.big_(p' in N(p)) t_(p',n-1)$, le point 1 tomberait :
    le solveur pourrait la satisfaire en mettant $t_(p',n-1)$ à vrai sans
    aucun qubit en $p'$. Il faudrait alors ajouter la réciproque.
]

= Nombre de clauses

#single_column_table(
  headers: ([Famille], [Formule], [$n = 100$, $P = 1961$]),
  content: (
    [1. Au moins un],
    [$n$],
    [100],
    [2. Au plus un emplacement],
    [$n (3P - 4)$],
    [587 900],
    [3. Au plus un qubit, occupation],
    [$P (3n - 2)$],
    [584 378],
    [4. Distance min],
    [$|D| approx 8P \/ 2$],
    [7 600],
    [5. Couronne CZ],
    [$m P$],
    [$<= 9.7$ M ($m <= 4950$)],
    [*Total*],
    [],
    [$approx 1.18$ M $+ m P$],
  ),
  false,
  none,
)

Pour comparer : l'encodage « au plus un » par paires coûtait
$n P (P-1) \/ 2 approx 192$ M clauses pour la famille 2, et
$P n (n-1) \/ 2 approx 9.7$ M pour la famille 3. La distance minimale
écrite par paire de qubits coûtait $approx 128$ M clauses.

= Questions ouvertes <ouvert>

- La valeur du seuil de la couronne.
- Le cassage de symétrie (fixer un qubit) : gain jugé faible. Les qubits
  « pivots » : idée mise de côté.
