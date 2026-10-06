#import "styles.typ": base-text-rules, colors, fonts

#let article(
  title: none,
  authors: (),
  abstract: none,
  keywords: (),
  date: auto,
  cols: 1,
  body,
) = {
  // --- Métadonnées document ---
  set document(
    title: title,
    author: authors.map(a => a.name),
  )

  // --- Règles globales (avant tout) ---
  base-text-rules()
  set heading(numbering: "1.1")
  set math.equation(numbering: "(1)")

  show heading.where(level: 1): it => {
    set text(font: fonts.serif, size: 12pt, fill: colors.primary, weight: "bold")
    v(1em)
    it
    v(0.5em)
  }
  show heading.where(level: 2): it => {
    set text(font: fonts.serif, size: 11pt, fill: colors.primary, weight: "bold")
    v(1em)
    it
    v(0.5em)
  }
  show math.equation.where(block: true): it => { it }
  show link: it => text(fill: colors.accent, it)

  // --- Pages liminaires (titre + abstract + sommaire) ---
  set page(
    paper: "a4",
    margin: (x: 2.5cm, top: 3cm, bottom: 3cm),
    numbering: none,
    header: none,
    footer: none,
  )

  // Page de titre
  align(center)[
    #image("../resources/quantum_logo.jpg", width: 70%)
    #v(0.5cm)
    #text(font: fonts.serif, size: 18pt, weight: "bold")[#title]
    #v(0.8cm)

    #let aff-map = (:)
    #for (i, a) in authors.enumerate() {
      if "affiliation" in a {
        aff-map.insert(a.affiliation, str(1))
      }
    }

    #(
      authors
        .map(a => {
          let sup = if "affiliation" in a { super[#aff-map.at(a.affiliation)] } else { [] }
          [#a.name#sup]
        })
        .join([, ])
    )

    #v(0.3cm)
    #text(size: 9pt, fill: colors.secondary)[
      #aff-map.keys().enumerate().map(((i, k)) => [#super[#str(i + 1)]#k]).join([; ])
    ]

    #v(0.3cm)
    #text(size: 9pt, fill: colors.secondary)[
      #if date == auto {
        datetime.today().display("[day] [month repr:long] [year]")
      } else { date }
    ]
  ]

  // Abstract
  if abstract != none {
    v(1cm)
    align(center)[
      #block(
        width: 85%,
        inset: 12pt,
        fill: colors.muted,
        radius: 4pt,
      )[
        #text(weight: "bold")[Abstract. ]
        #abstract
        #if keywords.len() > 0 [
          #parbreak()
          #text(weight: "bold")[Keywords : ]
          #keywords.join(", ")
        ]
      ]
    ]
  }

  pagebreak()

  // Sommaire
  page(
    numbering: none,
    header: none,
    footer: none,
  )[
    #outline(title: "Sommaire", depth: 2)
  ]

  counter(page).update(1)

  // --- Corps du document ---
  set page(
    paper: "a4",
    margin: (x: 2.5cm, top: 3cm, bottom: 3cm),
    numbering: "1",
    header: context {
      if counter(page).get().first() == 1 { return }
      let headings = query(
        selector(heading.where(level: 1)).before(here()),
      )
      let current-section = if headings.len() > 0 {
        headings.last().body
      } else { [] }

      set text(size: 8pt, fill: colors.secondary)

      if calc.odd(counter(page).get().first()) {
        grid(
          columns: (1fr, 1fr),
          align: (left, right),
          current-section, counter(page).display(),
        )
      } else {
        grid(
          columns: (1fr, 1fr),
          align: (left, right),
          counter(page).display(), text(style: "italic")[#title],
        )
      }
      line(length: 100%, stroke: 0.5pt + colors.border)
    },
    footer: context {
      set text(size: 8pt, fill: colors.secondary)
      align(center)[
        #counter(page).display("1 / 1", both: true)
      ]
    },
    columns: cols,
  )
  body
}
