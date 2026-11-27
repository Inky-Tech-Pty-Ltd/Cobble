# Room weight: transparent edge controls and rounded borders

*Cobble design decision — 26 November 2026. [Discussion and rationale: Issue #85](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/85). [Implementation: Candidate 3 PR #84](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/84).*

## Two jobs, two independent mechanisms

The convenor recognised that we were asking one painted crescent to do two jobs. A manually drawn curve at the left did not quite touch its object, and visually appeared *inside* the membrane, detached from the shape it was supposed to enclose.

**1. The transparent left-edge hit target is the control.** It is a real button attached to the card, with a tooltip, keyboard focus indication and `aria-pressed` semantics. It remains transparent in both states. Clicks still perform exactly the same room-governance operations as before.

**2. The object's own teal `border-left` is the visible state.** The original close-fitting effect was a 5px left border on the rounded object, not a diffuse shadow. An inactive object has no special weight border; an active one has it. Hovering a non-active edge gives a faint, temporary preview. The Chair, standing orders and the instance Membrane are structurally heavy and retain their own permanent weight border.

The *visual border* is common, but its operational meaning depends on the object. **Light** means ordinary participation; **heavy** means an expressly selected or constitutive role.

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

Human contributions, including prompts addressed to suppliers, and completed supplier replies with actual answers each get their own publication edge. A paired turn retains its original ledger ID; the human prompt uses that ID with a `:question` suffix for selection. Bare IDs retain their historical meaning (a local post or supplier answer). Selecting or withdrawing either half never changes the other. The restricted guest interface shows selected weight but has **no controls** to change it.

## Colour and accessibility

**One weight colour: teal (`#168A96`).** The 5px left border follows the element's actual rounded geometry. The earlier diffuse shadow, detached crescents and pseudo-element strokes are superseded.

The transparent left-edge button keeps its accessible label, `aria-pressed`, tooltip, pointer cursor and keyboard focus ring. A faint border preview appears on hover over an inactive edge; on click the solid border is activated by the existing state. No coloured pseudo-element is drawn along the edge. The guest view is read-only and draws the same borders for authorised messages, an admitted Door and the Chair.

The **Membrane** navigation item remains a soft teal bubble with a structural rounded border. A selected Room voice bubble, Joe's heavy default and a supplier holding the floor receive that border only while selected. The Chair and standing-orders object are always weight-bearing. Uninstalled templates in Furniture use normal borders rather than weight borders; available is not the same as deployed.

Supplier identity colours (for example Claude's pink icon) remain separate from the teal weight language. The background surfaces stay in Cobble's restrained neutral blue-grey palette, not broad orange or teal fills. Accessible labels explain the action independent of colour.

## Why we chose this

A weight-bearing utterance, a selected intelligence, a Door and standing orders are all different objects, but can be understood with a common visual vocabulary. Cobble's UI should explain the governance of Rooms through *the objects themselves*, rather than accumulating detached "Redact voice", "Give AI the floor" and "Joe: speak for room" buttons.

**Furniture is the catalogue; Membrane is the installation.** Furniture's Doors and Windows are **reusable templates**, not installed equipment. **Membrane → Doors** and **Membrane → Windows** represent the **actual objects deployed at the outer membrane of this Cobble instance**. A Room at a smaller scale has its own deployed furniture on its own membrane: the currently working invitation Door belongs to one meeting Room, and is operated from Meetings. Furniture can explain that Door's *template* without becoming the control surface for that deployed instance.

At present, the Membrane pages display honest empty installation states. They are **not backed by a deployed-instance registry**, installer, remote access-control editor or public publishing endpoint. The localhost operator service is not to be relabelled as a fully configured Door. Empty states must not claim to have queried a live registry. Adding an object to Furniture does not activate it; deploying a Door to a meeting does not grant admission at the enclosing Cobble instance's outer boundary. The submenu's expanded state is browser-local.

**The distinctions between template, deployed object, and membrane scope are separate.** This allows competing Door and Window designs to be reused in different Rooms, while each Room independently decides which concrete furniture it installs and operates. Neither these pages nor the visual metaphor grants a meeting guest access to private memories, unrelated Rooms or McKay's operator console.

## Implementation notes / verification

- Source: `src/cobble/static/workbench.html`, `src/cobble/static/guest_room.html`.
- Server governance (unchanged): `src/cobble/meeting_rooms.py`; restricted guest projection `scripts/snug_demo_web.py`.
- Tests: `tests/test_cobble_workbench.py`, `tests/test_snug_live.py`.
- Delivery: draft [PR #84](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/84); experimental local two-browser test first, no remote guest networking.
- This decision deliberately does **not** introduce a new generic property to the underlying Room model. We can revisit the abstraction after more than one Room type has working operational semantics.
