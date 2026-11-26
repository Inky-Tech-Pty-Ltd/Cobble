# Room weight: the left-edge language

*Cobble design decision — 26 November 2026. [Discussion and rationale: Issue #85](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/85). [Implementation: Candidate 3 PR #84](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/84).*

## What the crescent says

A thin **crescent at the left edge** tells us that an object can carry more weight than ordinary conversation. The *shape* is consistent, but the authority always belongs to the Room and to the role of the object. **Light** means ordinary participation; **heavy** means an expressly selected or constitutive role.

| Object | Light | Heavy | Who may change it? |
|---|---|---|---|
| A human's posted speech | Table talk | Selected in outward Room voice | Convenor, per bubble |
| A completed supplier reply | Table talk | Selected in outward Room voice | Convenor, per bubble |
| A supplier's seat/card | Present but not holding floor | Selected as the responding supplier for the next operator request | Convenor, per supplier |
| Joe's control at the top right | Joe's subsequent posts are ordinary by default | Joe's subsequent posts enter Room voice by default | Joe, by clicking the left edge |
| Chair / standing orders | Not applicable | Always structurally weight-bearing | Not toggled from the edge |
| A Room Door or the instance Membrane | Not applicable | The location of an admission boundary | Door controls govern admission separately |

This is **one visual grammar for related operations**, not a single universal "permission" property. Moving the floor never authorises a past utterance; publishing a contribution never grants a participant future precedence.

## Controls and consequences

The left edge of each eligible speech bubble is an actual, keyboard-accessible button with descriptive `aria-label` and `aria-pressed` state. The convenor may click it to select, withdraw or restore that particular contribution to the Room's outward voice. The backend uses the pre-existing `voice_event` / `redact_event` governance operations. Redaction here means withdrawal **from outward voice**, **not** removal from the immutable internal event ledger.

On supplier cards, the edge chooses or releases the **floor** for the next message; it does not call an API until the convenor explicitly presses Send. Unavailable or uninvited suppliers cannot receive the floor. The rest of a supplier card still handles membership, and the details button still inspects cost and context; they are not hidden behind a generic toggle.

Joe's header card controls his **local default posting mode**. Individual subsequent bubbles can be reassessed; earlier posts do not change when he switches the default. The mode currently lasts only in this browser for the current meeting session. It is neither autonomous Chair policy nor persistent permission state.

The Chair and standing orders always appear heavy because they govern the table. **Heavy does not mean externally published.** Standing orders are supplied as context where authorised; they are not inserted into the Room's outward output.

Only eligible events get a publication edge: locally posted human contributions and completed supplier replies with actual answers. A prompt addressed to a supplier is not independently publishable with the present paired-turn event model; its *reply* can be selected. The restricted guest interface shows selected weight but has **no controls** to change it.

## Colour and accessibility

**One crescent, one colour: teal (`#168A96`).** Earlier orange and blue experiments, including different crescent colours for participants, have been superseded. A crescent means the same visual kind of weight everywhere: admission at a membrane, an authorised utterance, the holder of the floor, a default voice mode, or a structural standing order. Its *action* still depends on the object, but its shape and colour do not. Supplier identity colours (for example Claude pink) may survive inside identity icons, **not** on the weight crescent.

**The crescent hugs the object's outside-left contour**, rather than sitting as a decorative vertical line *inside* its padding. The curve should read as enclosing or protecting the object. The compact Membrane navigation item is therefore a soft teal bubble, with the same curved outside edge even when the Membrane page is not selected. Guest speech, admission status, Joe's header card, the Chair, the supplier seats, the Door button, and the standing orders use the same shared teal rule. Heavy and light are encoded through opacity/strength, with a keyboard-accessible hit target where the edge is actionable.

The background surfaces stay in Cobble's restrained neutral blue-grey palette. Do **not** turn them into large teal, blue or orange fills.

The interface must also communicate this distinction **without relying on colour alone**: left-edge shape, strength, hover, focus ring, title tooltip, and accessible labels. Fixed heavy accents are not interactive controls.

## Why we chose this

A weight-bearing utterance, a selected intelligence, a Door and standing orders are all different objects, but can be understood with a common visual vocabulary. Cobble's UI should explain the governance of Rooms through *the objects themselves*, rather than accumulating detached "Redact voice", "Give AI the floor" and "Joe: speak for room" buttons.

The Membrane navigation entry represents **this Cobble instance's own boundary**. Smaller Doors reside under **Furniture → Doors**. Neither the visual treatment nor this decision grants an invited meeting visitor access to private memories, other rooms or the McKay operator console.

## Implementation notes / verification

- Source: `src/cobble/static/workbench.html`, `src/cobble/static/guest_room.html`.
- Server governance (unchanged): `src/cobble/meeting_rooms.py`; restricted guest projection `scripts/snug_demo_web.py`.
- Tests: `tests/test_cobble_workbench.py`, `tests/test_snug_live.py`.
- Delivery: draft [PR #84](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/84); experimental local two-browser test first, no remote guest networking.
- This decision deliberately does **not** introduce a new generic property to the underlying Room model. We can revisit the abstraction after more than one Room type has working operational semantics.
