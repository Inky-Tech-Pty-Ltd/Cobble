"""Deterministic A0/A1/A2 memory-graph evaluation. No network, models or private data.

A0: keyword-ranked flat traces. A1: graph-filtered keyword-ranked traces.
A2: A1 plus source-availability observations. The experiment intentionally
separates retrieval relevance from evidence-state reporting.
"""
import json
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "memory_graph" / "corpus.json"


def load_corpus(path=FIXTURE):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ids = [x["id"] for x in data["traces"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate trace IDs")
    known = set(ids)
    for query in data["queries"]:
        if query["anchor"] not in known or not set(query["relevant"]) <= known:
            raise ValueError("Unknown query references")
    for group in data["stars"]:
        if not set(group["members"]) <= known:
            raise ValueError("Unknown star member")
    return data


def tokens(value):
    import re
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def ranking(data, query, architecture):
    """Same lexical scoring, same candidates, same budget for all arms.

    A1/A2 gain only an asserted link bonus when anchor and candidate
    occur in the same star. These labels are synthetic experimental inputs,
    not inferred or verified equivalence claims.
    """
    anchor = query["anchor"]
    neighbor_ids = set()
    if architecture != "A0":
        for star in data["stars"]:
            if anchor in star["members"]:
                neighbor_ids.update(star["members"])
    query_tokens = tokens(query["text"])
    ranked = []
    for item in data["traces"]:
        if item["id"] == anchor:
            continue
        lexical = len(query_tokens & tokens(item["text"]))
        link_bonus = 2 if item["id"] in neighbor_ids else 0
        ranked.append((-(lexical + link_bonus), item["id"]))
    return [identifier for _, identifier in sorted(ranked)]


def outcomes(data, architecture, k=4):
    if architecture not in {"A0", "A1", "A2"}:
        raise ValueError("Unknown architecture")
    results = []
    for query in data["queries"]:
        returned = ranking(data, query, architecture)[:k]
        relevant = set(query["relevant"]) - {query["anchor"]}
        hits = len(relevant.intersection(returned))
        results.append({
            "query": query["id"], "retrieved": returned,
            "relevant_found": hits,
            "precision_at_k": hits / k,
            "recall_at_k": hits / len(relevant) if relevant else 1.0,
        })
    return results


def observation_report(data, architecture):
    """Source status is only available in A2, including historical observations."""
    if architecture not in {"A0", "A1", "A2"}:
        raise ValueError("Unknown architecture")
    result = {}
    for item in data["traces"]:
        timeline = data["observations"].get(item["id"], []) if architecture == "A2" else []
        result[item["id"]] = {
            "last_seen_status": timeline[-1]["status"] if timeline else "unknown",
            "historical_available": any(x["status"] == "available" for x in timeline),
        }
    return result


def evaluate(data=None):
    data = data or load_corpus()
    rows = {}
    for arch in ("A0", "A1", "A2"):
        scores = outcomes(data, arch)
        rows[arch] = {
            "mean_precision_at_4": round(sum(x["precision_at_k"] for x in scores) / len(scores), 4),
            "mean_recall_at_4": round(sum(x["recall_at_k"] for x in scores) / len(scores), 4),
            "per_query": scores,
        }
    statuses = {arch: observation_report(data, arch) for arch in ("A0", "A1", "A2")}
    observed_ids = sorted(data["observations"])
    rows["availability"] = {
        "observed_traces": observed_ids,
        "history_recovered_by_architecture": {
            arch: sum(1 for ident in observed_ids if statuses[arch][ident]["historical_available"])
            for arch in ("A0", "A1", "A2")
        },
        "last_status": {arch: {ident: statuses[arch][ident]["last_seen_status"]
                              for ident in observed_ids} for arch in ("A0", "A1", "A2")},
    }
    rows["ablation"] = {
        "remove_links_equals_A0": all(
            ranking({**data, "stars": []}, q, "A1") == ranking(data, q, "A0")
            for q in data["queries"]),
        "remove_observations_equals_A1_reporting": all(
            observation_report({**data, "observations": {}}, "A2")[x]["last_seen_status"]
            == observation_report(data, "A1")[x]["last_seen_status"]
            for x in observed_ids),
    }
    return rows


def main():
    print(json.dumps(evaluate(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
