// Palette de couleurs
#let colors = (
  primary: rgb("#000"),
  secondary: rgb("#64748b"),
  accent: rgb("#0ea5e9"),
  muted: luma(245),
  border: luma(220),
)

// Typographie
#let fonts = (
  serif: "New Computer Modern",
  sans: "New Computer Modern",
  mono: "New Computer Modern",
  math: "New Computer Modern Math",
)

// Règles globales réutilisables
#let base-text-rules = () => {
  set text(font: fonts.serif, size: 8pt, lang: "fr")
  set par(justify: true, leading: 0.65em)
  set math.equation(numbering: "(1)")
}

#show raw.where(block: true): set block(
  fill: rgb("#f8f9fa"),
  inset: 8pt,
  radius: 4pt,
)

#show raw: it => {
  set text(font: "JetBrains Mono", size: 8pt)
  it
}
