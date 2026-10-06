#import "styles.typ": colors, fonts

// Compteurs
#let thm-counter = counter("theorem")
#let def-counter = counter("definition")
#let lem-counter = counter("lemma")

// Composant de base générique
#let _block-component(
  name,
  counter,
  color,
  body,
  title: none,
) = {
  counter.step()

  block(
    width: 100%,
    inset: (x: 12pt, y: 10pt),
    radius: 4pt,
    fill: color.lighten(90%),
    stroke: (left: 3pt + color),
  )[
    #text(weight: "bold", fill: color)[
      #name #context counter.display()
      #if title != none [ (#text(style: "italic")[#title])]
    ]
    #parbreak()
    #body
  ]
}

#let theorem(body, title: none) = _block-component(
  "Théorème",
  thm-counter,
  colors.primary,
  body,
  title: title,
)

#let lemma(body, title: none) = _block-component(
  "Lemme",
  lem-counter,
  colors.accent,
  body,
  title: title,
)

#let definition(body, title: none) = _block-component(
  "Définition",
  def-counter,
  colors.secondary,
  body,
  title: title,
)

#let proof(body) = block(inset: (left: 12pt))[
  #text(style: "italic")[Proof.]
  #body
  #h(1fr) $square$
]

#let remark(body) = block(inset: (left: 12pt))[
  #text(weight: "bold")[Remarque.]
  #h(4pt)
  #body
]

#let single_column_table(headers: (), content: (), float, caption) = {
  let tab = figure(
    {
      set text(size: 10pt)
      table(
        columns: headers.len() * (1fr,),
        stroke: 0.4pt + luma(160),
        fill: (x, y) => if y == 0 { rgb("#1a3a5f") } else if calc.even(y) { rgb("#f0f4fa") } else { white },
        inset: (x: 8pt, y: 5pt),
        align: left,
        table.header(..headers.map(h => table.cell[#text(fill: white, weight: "bold")[#h]])),
        ..content,
      )
    },
    caption: if caption != none { [#caption] } else { none },
  )

  if (float) {
    place(
      auto,
      float: true,
      scope: "parent",
      align(center, tab),
    )
  } else {
    v(0.5em)
    tab
    v(0.5em)
  }
}

#let hbar = text(style: "italic")[\u{0127}]
#let ket(x) = $lr(|#x chevron.r)$
#let bra(x) = $lr(chevron.l #x|)$
