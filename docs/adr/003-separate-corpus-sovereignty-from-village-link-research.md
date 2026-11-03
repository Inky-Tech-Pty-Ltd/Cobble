# ADR-003: Separate corpus sovereignty from Village Link research

**Date:** 4 November 2026  
**Status:** Accepted  
**Project:** Cobble

## Context

Cobble's development has entangled two distinct propositions:

1. **Corpus sovereignty:** A persistent body of memory can be maintained independently of its suppliers of intelligence. Intelligence providers can be connected, disconnected and replaced without losing the corpus.
2. **Village Link memory architecture:** A graph of Village Links may improve retrieval, salience, compression and memory management.

The second proposition is an interesting research hypothesis, but proving it would require comparison against substantial existing work in search, information retrieval and compression.

The first proposition does not depend on the second.

## Decision

**Prioritise demonstrating corpus sovereignty independently of Village Link research.**

For the immediate Cobble implementation:

- Maintain a persistent, independently controlled, searchable corpus.
- Support ingestion and ongoing synchronisation from multiple memory sources.
- Support interchangeable suppliers of intelligence through provider-independent interfaces.
- Use established technologies for storage, search, retrieval and compression.
- Do not require Village Links, salience algorithms, adaptive forgetting or artificial memory scarcity.
- Retain ordinary operational limits on cost, storage, permissions and resource consumption.

## Consequences

The immediate objective is to demonstrate that an entity can preserve and use its memories across changes of intelligence provider.

Village Link graph retrieval, salience, compression and resource-constrained memory remain available as independent research programmes. Existing work is preserved.

These mechanisms may later be incorporated into Cobble where experiments demonstrate sufficient value.

**Their success is no longer a prerequisite for demonstrating Cobble's core value proposition.**
