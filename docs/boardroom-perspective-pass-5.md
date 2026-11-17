# Boardroom perspective pass 5 — same camera, all objects

This pass responds to the operator's visual evaluation of the Draw.io-based
room on 17 November 2026. **The whole scene, including readable text, must
respect a single perspective.** A merely tilted text box is not enough.

## Invariants

- **Do not re-invent the room:** retain the source-derived floorboard rays,
  burgundy wall, left glazed hall, physical eight-vertex slate tabletop,
  and persistent API/ledger/privacy machinery.
- The table is the scarce resource for conversation. Widen the table from
  52.1875% to 58% of stage width, preserving its profile, orientation and
  floor relationship. Move the suppliers in toward the table edge.
- GPT (far left) appears above, inward and **smaller** than Claude (near left).
  Claude sits diagonally closer to the viewer, not directly under GPT.
  Mistral is near right and has similar apparent scale to Claude. Seated
  figures are still editable SVG illustrations, not photographs.
- The speaker tail has two perimeter routes: left suppliers via the upper
  wall and the left corridor edge; Mistral via the right side of the table.
  Snug gets a short top-of-table arc. The white line is less dominant.
- Folder and mouse are rendered as shallow, foreshortened inline SVGs:
  the folder follows the operator's bright yellow rounded Paint drawing;
  the mouse is a low oblique oval with shell, seam, wheel and contact shadow.
  Both remain real clickable controls.

## Why a homography matters

The earlier version used \`rotateX(9deg)\` on a rectangular transcript box
inside a differently shaped table. That produced readable text but not a
consistent plane. The browser now calculates a **four-corner projective
transform**, applied through CSS \`matrix3d\`, mapping the transcript
rectangle to a quadrilateral inset within the actual tabletop:

| Corner | Normalised table-space x,y |
|---|---|
| Far left | (0.253, 0.145) |
| Far right | (0.860, 0.145) |
| Near right | (0.888, 0.846) |
| Near left | (0.126, 0.846) |

The homography is recalculated at first paint, after fonts settle, and
on viewport resize. The far edge is narrower and the near edge wider.
Glyph scale and row position vary continuously with depth.

This is still not a full 3D engine: hands, feet, objects and shadows
are individual vector assets that need operator visual acceptance in
McKay's Chrome window. The goal here is that perspective is **structurally
testable** rather than a series of unrelated artistic approximations.

## Scope of acceptance

Check that:
1. Near participants are visibly larger and seated on the receding edges.
2. Text narrows to the far end and enlarges continuously toward the viewer.
3. Mouse and yellow folder read as physical tabletop objects.
4. Speech-tail no longer crosses the conversation.
5. Mouse-wheel history, document filename staging, supplier calling,
   disclosure padlocks and audit panes still work.

**No model prompt, server permissions, supplier API, or context-sharing
semantics were changed.** In/out is still a browser-level convenience,
not server-enforced confidentiality.
