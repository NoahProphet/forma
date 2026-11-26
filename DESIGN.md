---
name: FORMA
description: Persian RTL storefront for kitchen, bath, and building finishes.
colors:
  gold: "#dabc94"
  paper: "#f8f5ee"
  ivory: "#fffcf6"
  stone: "#ede5d7"
  line: "#d5c9b8"
  ink: "#201d19"
  muted: "#645b50"
  dark: "#231f1b"
  focus: "#745026"
typography:
  display:
    fontFamily: "Vazirmatn, Tahoma, sans-serif"
    fontSize: "clamp(2.5rem, 3.65vw, 3.75rem)"
    fontWeight: 765
    lineHeight: 1.21
  headline:
    fontFamily: "Vazirmatn, Tahoma, sans-serif"
    fontSize: "clamp(2rem, 3.8vw, 3.5rem)"
    fontWeight: 720
    lineHeight: 1.25
  section-title:
    fontFamily: "Vazirmatn, Tahoma, sans-serif"
    fontSize: "clamp(1.5rem, 2.8vw, 2.35rem)"
    fontWeight: 720
    lineHeight: 1.25
  title:
    fontFamily: "Vazirmatn, Tahoma, sans-serif"
    fontSize: "1.1rem"
    fontWeight: 720
    lineHeight: 1.35
  body:
    fontFamily: "Vazirmatn, Tahoma, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.75
  small:
    fontFamily: "Vazirmatn, Tahoma, sans-serif"
    fontSize: ".8125rem"
  meta:
    fontFamily: "Vazirmatn, Tahoma, sans-serif"
    fontSize: ".875rem"
  ui:
    fontFamily: "Vazirmatn, Tahoma, sans-serif"
    fontSize: ".9375rem"
  action:
    fontFamily: "Vazirmatn, Tahoma, sans-serif"
    fontSize: ".9375rem"
    fontWeight: 640
    lineHeight: 1.5
rounded:
  square: "0"
  circle: "50%"
spacing:
  gutter: "clamp(18px, 4.7vw, 72px)"
  section: "clamp(52px, 6vw, 88px)"
  inline-control-gap: ".65rem"
components:
  button-primary:
    backgroundColor: "{colors.dark}"
    textColor: "{colors.ivory}"
    typography: "{typography.action}"
    rounded: "{rounded.square}"
    padding: ".7rem 1.3rem"
  button-gold:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.ink}"
    typography: "{typography.action}"
    rounded: "{rounded.square}"
    padding: ".7rem 1.3rem"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.action}"
    rounded: "{rounded.square}"
    padding: ".7rem 1.3rem"
  input-text:
    backgroundColor: "{colors.ivory}"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
    padding: ".45rem .65rem"
  navigation:
    backgroundColor: "{colors.ivory}"
    textColor: "{colors.ink}"
    height: "74px"
  catalog-tab:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.meta}"
    height: "44px"
  category-chip:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.meta}"
    rounded: "{rounded.square}"
    height: "44px"
  category-chip-selected:
    backgroundColor: "{colors.dark}"
    textColor: "{colors.ivory}"
    typography: "{typography.meta}"
    rounded: "{rounded.square}"
    height: "44px"
  product-card:
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
  finish-swatch:
    textColor: "{colors.ink}"
    typography: "{typography.small}"
    rounded: "{rounded.square}"
    padding: ".4rem .45rem"
  equipment-index-link:
    textColor: "{colors.ink}"
    typography: "{typography.ui}"
  project-product-link:
    textColor: "{colors.ink}"
    typography: "{typography.ui}"
---

# Design System: FORMA

## Overview

**Creative North Star: "The Material Showroom"**

FORMA gives kitchen and bath equipment the presence it has in a physical showroom. Material photography occupies its own space alongside Persian headings and copy. Warm paper, ivory, and stone frame the images. Fine rules and square edges organize the controls.

Product types provide a direct way into the catalog. One featured product gets an editorial treatment that puts material and finish choices beside a photograph. Project pages connect installation photography and prose to the equipment shown.

**Key Characteristics**

- Persian-first hierarchy in Vazirmatn.
- Separate photography and copy with a dedicated mobile hero crop.
- Finish samples with visible names and a current-state underline.
- Matte-black shopping actions with small warm-metal accents.

## Colors

### Primary

- **Champagne Gold** fills the showroom visit action and text selection. It also marks keyboard focus on the dark showroom band and footer.

### Neutral

- **Paper** is the default page canvas. **Ivory** is the navigation, input, disclosure, and selected finish surface, as well as the light foreground on dark controls.
- **Stone** groups hero copy and photography, product galleries, the cart count, and order summaries. **Line** subdivides rows and frames imagery and quiet controls.
- **Ink** carries primary text. **Muted** carries captions, metadata, and supporting copy.
- **Dark** fills primary shopping actions and the showroom visit band. The footer uses a deeper shade in the same warm range.
- **Focus** supplies brown accent marks on light surfaces, including navigation underlines, equipment arrows, selected finishes and thumbnails, and keyboard outlines.

**The Champagne Accent Rule.** Use matte dark fill for browsing and purchase actions. Keep champagne fill for the showroom visit action and use the darker metal tone for small marks and rules on light surfaces.

## Typography

Vazirmatn supplies Persian and Latin characters throughout. The two local variable-font subsets share a weight range of 100–900 and fall back to Tahoma, then sans-serif.

### Hierarchy

- **Display** (765, 2.5–3.75rem, 1.21 line height) heads the desktop hero. At 767px and below it uses `clamp(2.1rem, 7.7vw, 3.15rem)`.
- **Headline** (720, 2–3.5rem, 1.25 line height) titles interior pages. The purchase title uses `clamp(2rem, 3.45vw, 3.45rem)`.
- **Section title** (720, 1.5–2.35rem, 1.25 line height) marks section breaks. **Product card title** (720, 1.1rem, 1.35 line height) moves to the UI size at 640px and below.
- **Body** (16px, 1.75 line height) serves functional copy. Editorial prose uses a more open 1.95 line height. Project prose is capped at 64ch.
- **Small** (13px) serves breadcrumbs, finish tile labels, and stock text. **Meta** (14px) serves catalog metadata, filter labels, and result counts. **UI** (15px) serves buttons, navigation, and text actions. These are the three shared compact type steps.
- Prices use tabular numerals (730) with a smaller unit (.75em, 550).

**The Persian Reading Order Rule.** Set the page direction to RTL and isolate mixed-direction identifiers such as Latin brand names, models, and SKUs with `bdi`.

## Layout

Shared rows and sections align to a centered frame capped at 1320px. Fluid side gutters run from 18px to 72px. Major sections use a fluid block rhythm of 52–88px.

- On desktop, the stone hero band places copy at inline start beside a larger 1.72:1 image with a cover crop. At 767px and below, the image sits above the copy in a 1.39:1 frame. At 640px and below, the image element switches to the dedicated mobile source.
- The product-type index follows directly below the hero. Its links use full-width ruled rows in a flexible desktop grid and two columns at 767px and below. The featured-product split follows, with small labeled finish samples beside the photograph.
- On wider screens, a 175–232px filter rail sits at inline start beside the three-column catalog. At 1020px and below the cards use two columns. At 767px and below, the filter form moves into a drawer when dialog enhancement is available.
- The desktop product page places the narrower purchase column at inline start and the larger gallery beside it. The 1.43:1 gallery uses contain fit. At 767px and below the gallery stacks before purchase details. At 640px and below it switches to a 1.4:1 cover frame and smaller thumbnails.
- Project details use a split title and summary, a full-width cover, and a prose column beside the products list. Detail images wrap in a row on desktop and stay within their native dimensions. At 767px and below the project sections stack and the cover moves from 2.07:1 to 1.5:1.

## Elevation & Depth

Stone-to-paper transitions, photography, and hairline rules establish depth on main surfaces. Search and mobile navigation disclosures use a diffuse shadow (`0 12px 20px #211b101c`). The mobile filter drawer dims the underlying page with a warm dark backdrop. The 2px inset strokes on selected gallery controls mark selection.

**The Flat Surface Rule.** Let alignment, borders, and tonal layering organize repeated cards. Save cast shadows for overlays.

## Shapes

Buttons, input borders, media frames, and finish controls use square corners. Hairline borders are typically 1px. The small cart count is circular. Finish samples use square markers in the catalog and home feature and short rectangular bars in product detail tiles.

## Components

### Buttons and links

- Primary controls use ivory text on dark fill and a minimum block size of 48px, with a 44px hero action on mobile. The dark showroom band carries its gold visit control. Outline controls use a single border and a stone hover fill.
- Filled and outline buttons shift up 2px on hover and down 1px on activation. Inline actions can use an underline on hover. Text links and icon controls generally offer a 44px target.
- Focus uses a 2px outline with a 4px offset. The outline is brown on light surfaces and gold on the dark showroom band and footer. Reduced motion suppresses the entrance and transition durations.

### Category tabs and chips

Catalog tabs share a baseline rule. The selected tab uses a 2px brown underline and stronger type. Other inquiry forms use square outlined chips with a dark selected fill.

### Catalog cards

Cards pair a bordered 1.34:1 cover photograph with a product title, brand/model metadata, and a finish name with an 11px square sample when a finish color exists. A top rule separates price and stock from the metadata. Comparison remains a compact text action. The product image scales to 1.025 on hover.

### Inputs

Ivory fields use square corners, a 1px border, and a 44px minimum block size. Labels sit above fields. Error text and invalid input borders use warm red. Numeric filter fields isolate input direction and align to the right.

### Navigation

A single ivory header uses a wordmark, primary links, search, and bag controls. On wider screens a showroom location link sits beside the wordmark. It is hidden at 1020px and below. Current and hovered destinations use warm underlines. At 767px and below, the 62px row keeps the logo centered between the menu disclosure and the search and bag controls.

### Finish selection and gallery

The finish group sits between horizontal rules. Tiles have a minimum height of 58px and show a visible finish name with a 28 × 12px color sample where available. The current tile has an ivory fill and a dark brown border and inset underline. Active thumbnails use the same border and underline treatment.

Selecting a finish updates the gallery, SKU, price, availability, purchase or quote action, and finish specification together. Finish choices are links so the selected option has a URL and works through a full page request. Thumbnail links retain the selected finish. With enhancement, the same links update the view in place and restore focus to the control after the swap.

### Editorial product and project lists

The home feature pairs a 1.4:1 product image with the product name, available material or size, and a two-column finish list when variants exist. Each finish row links to the corresponding product choice. The project products list uses ruled links, optional 68px thumbnails and model codes, and arrows aligned to inline end.

## Do's and Don'ts

- **Do** give hero and editorial copy space beside or below the photograph.
- **Do** pair finish colors with visible labels and keep current-state marks visible.
- **Do** use tabular Persian prices and isolate Latin model and SKU text.
- **Don't** add cast shadows to repeated catalog cards.
- **Don't** use gold fill for catalog and purchase actions.

