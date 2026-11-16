# Boardroom · perspective pass (16 November 2026)

This second visual iteration implements the operator's 16 November spatial
brief. It deliberately preserves the working live supplier routes and local
append-only conversation ledger.

## Camera and stage

- One-point **virtual camera** with vanishing point at scene coordinate
  **(800, 284)** in a responsive 1600×900 stage.
- Back-wall windows, the floor grid, the left-hand glazed corridor and door
  are drawn as a shared architectural projection.
- The **tabletop and all its writing are on the same CSS 3D plane** using
  \`perspective(94.5vh) rotateX(54deg)\`. This makes the text itself
  smaller upstage. Older utterances are allowed to become tiny.
- The scene is deliberately illustrative and not photorealistic; Snug and
  suppliers use simple inlined half-body SVG portraits with provisional
  appearances. These are interface characters, not real-person likenesses.
- The table mouse and manila document folder live on the same projected
  plane, with roughly plausible relative size.

## Current utterance and conversation

The **current-speaker panel** is fixed top-right and has a tail drawn to
the current character. Text inside it scrolls normally. As soon as the
operator starts typing outside a dialog/control, or clicks the panel,
the speaker becomes **Snug**, and the box becomes the editor. Once the
existing single-supplier API call completes, the reply takes over this
panel and Snug's question and the reply remain on the tabletop. There
are no duplicate participant speech bubbles.

History has no visible scrollbar. Click the **mouse object** on the
near-right tabletop to activate wheel navigation, then wheel over the
room to move through the retained conversation. Click the mouse again
or press Escape to release; keyboard users can focus the transcript
and use arrow/Page Up/Page Down keys.

The manila folder still opens a name-only staging dialog. No file
bytes are inspected or disclosed to an intelligence.

## Supplier and boundary invariants

- Live GPT / Claude / Mistral, provider-specific estimated charges,
  immutable pre-call snapshot, request/attempt/outcome ledger, and
  automatic selection by leading spoken name **remain unchanged**.
- There is still **one selected supplier response**, not autonomous
  interruptions. A long call waits in the current-speaker panel.
- The speaker panel has one Send arrow. Client performs the existing
  bounded-context preview and one-shot approved execution in sequence.
  This is not a new route for sharing corpus documents.
- The corridor is a visual, browser-only participation control until
  membership and heard-history are enforced by the server.
- Meeting beginning/end, real per-meeting costing, supplier autonomy,
  avatar customisation and real tabled-document contents are not in
  this pass.
- The private paired audit panes remain available behind each padlock.

## Test plan

1. Offline CI: Python regression suite, Node syntax validation of the
   inlined browser script, and static checks for the scene, speaker box,
   folder/mouse and unique document control IDs.
2. McKay: restart/reload the loopback server and visually inspect the
   16:9 desktop layout, perspective geometry, speech-tail attachment,
   transcript legibility and wheel scrolling.
3. One low-cost live utterance, followed by padlock inspection, to check
   that the UI works with the existing real ledger.

**Do not infer** that entering the corridor prevents a supplier from
receiving older persisted context; that requires a separate security
change. The meaningful advance here is a clearer spatial meeting UI.


## Pass 3 composition correction — 16 November 2026

Follow-up from the operator's latest pencil sketch and the fictitious boardroom
committee's reluctant vote to give Puck another attempt:

- The table is deliberately **nearly rectangular**. The displayed tabletop
  and transcript now use a shallow `perspective(1600px) rotateX(18deg)`
  projection rather than the previous dramatic steep plane. This prioritises
  usable conversation width while still letting older lines recede.
- The backdrop depicts a **windowless interior room**, with subdued wall
  panels and flooring. The distracting skyline has been removed.
- The glazed corridor remains on the **left**, but now occupies only about
  13.5% of the width. Waiting suppliers are drawn smaller.
- GPT, Claude and Mistral are **larger and anchored along the table edges**.
  The illustrated half-body characters now have chair backs, arms and small
  forward hands to communicate seating, not floating portraits.
- Snug remains at the head; the current speaker box is still upper-right,
  with the same owner-switching, scrollable text, and moving tail.
- The manila folder, tabletop wheel-mouse, meeting ledger, API supplier
  calls, private padlock view and local append-only records are **unchanged**.

This is an illustrated static scene, not a photorealistic render or a
physically simulated camera. The HTML view must still be evaluated visually
on McKay at its actual browser size; green CI alone cannot validate
foreshortening and character placement. No server permissions or autonomy
have been added in this visual correction.
