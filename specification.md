# Specification

This is an evolving sketch of Cobble's intended behaviour, not a claim that
all the capabilities below have been built. For tested progress, see
[docs/progress.md](docs/progress.md).

## Proposition

Cobble tests whether Village Links can connect scattered traces in the
memory systems shared by a person and an AI work-partner. Might the resulting
memory graph support a coherent, portable entity with a reputational asset?
Might resource dependence and consequences make that entity governable?

These are hypotheses, not demonstrated outcomes.

## Working architecture

A useful way of organising the problem is:

**Memory systems → traces → Village Links → connected graph → services**

- **Memory systems** may remain external (for example, ChatGPT or GitHub),
  or may have content preserved in a user-controlled store.
- **Traces** are addressable occurrences in memory systems. Cobble can give
  locally preserved passages stable trace URIs without changing the identities
  of their original sources.
- **Village Links** assert equivalence between traces. Publication of an
  assertion does not establish its truth.
- **The graph** is formed by maintained links among traces. Whether it can
  constitute a persistent, coherent entity is the experiment.
- **Services** may ingest, preserve, inspect, search, suggest links, retrieve,
  economise and expose memory. They are not new Village Link primitives.

Keep three roles distinct: **the memory store** (held under the customer's
control), **the Cobbler** (software maintaining and using it), and
**intelligence services** (which may change providers or running instances).
The current prototype exposes three read-only operations through a Cobble MCP
server on McKay. A ChatGPT plugin has successfully queried the local store
through a workspace-scoped secure tunnel. This proves a path for memory
access, not continuous assistant identity or autonomous memory maintenance.
See [the MCP experiment](docs/mcp.md) for the boundary and limitations.

## Application

1. Establish the customer's preferred store and its control boundaries.
2. Establish a backup and restoration approach.
3. Identify the sources of memory:
   1. Which traces remain in the wild?
   2. Which content should be synchronised or preserved locally?
   3. How are source identity, local copy and retrieval kept distinct?
4. Ingest without assuming that matching words imply matching memes.
5. When the customer's bot is sleeping, trigger a service called the
   **Cobbler** to:
   1. Search preserved and accessible memories.
   2. Identify tentative matches.
   3. Propose or maintain Village Links, retaining scope for judgement.
6. Explore resource stewardship: storage, bandwidth, computation, energy and
   the costs of retention or forgetting.
7. Explore other services, including the earlier **Dustman** idea (scrutinising
   links) and **BFG** idea (introducing surprising candidate connections).
   Their names, boundaries and value remain speculative.

## Design restraint

Our instinct is to learn the lesson of AlphaZero and avoid additional
structures where possible. Whenever a structure is proposed, ask:

> But might that be a meme? Should we really build this from the outside,
> when maybe it belongs on the inside?

The primitive should not inherit mandatory truth scoring, fixed types,
reputation rules or governance structures merely because a service might
find them useful.
