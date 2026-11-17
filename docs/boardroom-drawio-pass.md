# Boardroom composition pass 4 — operator's Draw.io geometry

This pass uses the **16:9, 1600 × 900** reference drawing supplied in
conversation as an architectural constraint. It does not ask the browser
to invent a second, independent perspective from a CSS rectangle.

## Fixed source geometry

- Stage: \`0,0\` through \`1600,900\`.
- Burgandy far wall: source rectangle \`x=202,y=0,w=1398,h=177\`.
- Left glazed partition: source polygon in a \`290 × 960\` box,
  with a leading tip at \`(90,0)\` and lower edge approaching \`(0,897)\`.
- Floorboard joint construction: source rays from approximately
  \`(1040,-2810)\`, **clipped** to the usable floor. They need not be
  shortened or discarded in the original Draw.io document.
- Slate tabletop: source \`x=307,y=134,w=835,h=665\`. Its eight
  normalised vertices are
  \`(0.9,0) (0.95,.04762) (.96698,.94769) (.91047,1)
  (.05,1) (0,.94552) (.14699,.03475) (.18883,0)\`.
  Four corners use short SVG curves preserving the principal edges.
- Snug stays at the far end, supplier seating is on the two long
  edges, and a narrow visual corridor remains left.
- Current-speaker panel stays upper right; the panel is UI overlay,
  not a painted object on the table.

## Rendering decisions

- The tabletop itself is a source-derived SVG path, with thickness,
  hints of legs, soft reflections and shadow; it is **not** independently
  CSS-rotated. This prevents a different camera from showing up in
  the table/floor relationship.
- Existing HTML transcript is projected a **shallow nine degrees**
  within the slate polygon. It remains scrollable and interactive.
- Supplier portraits at the table are new side-profile vector
  silhouettes with visible chairs, foreshortened torsos, ears/noses
  and hands. Corridor participants retain the smaller frontal
  portraits to avoid confusing entrance/exit controls.
- Mouse and manila folder are still functional HTML controls, but
  now tilted sharply towards the tabletop plane and made wide enough
  to register as physical objects rather than badges.
- Existing window glass, floorboards, burgundy wall and speaker
  panel proportions are taken from the operator's sketch, subject
  to responsive viewport adaptation.

## Unchanged and limitations

Only the static HTML/CSS/SVG/browser-side portrait function changed.
The append-only conversation ledger, API selection, supplier costs,
per-invocation context audit, one-shot preview approval and
document-filename-only staging are untouched. In/out remains a
**browser-level choice, not server-enforced confidentiality**.

The SVG is designed for a 1600x900 reference stage, but the actual
Chrome content area may be wider than 16:9. The room stage scales to
fit available pixels while HTML labels retain readable font sizes.
This is an illustration-driven UI, not a 3D engine. A real browser
screenshot and user review remain necessary: CI verifies structure
and JavaScript validity, not the visual believability of hands,
chairs, shadows or contact points.
