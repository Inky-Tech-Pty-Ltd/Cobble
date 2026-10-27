"""Independent-label A0/A1 benchmark with imperfect and adversarial graph edges."""
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
CORPUS=ROOT/"tests"/"fixtures"/"memory_graph"/"independent_corpus.json"
ANN=ROOT/"tests"/"fixtures"/"memory_graph"/"independent_annotations.json"

def load():
    corpus=json.loads(CORPUS.read_text(encoding="utf-8"))
    annotations=json.loads(ANN.read_text(encoding="utf-8"))
    ids={x["id"] for x in corpus["traces"]}
    qids={x["id"] for x in corpus["queries"]}
    if set(annotations["relevance"]) != qids:
        raise ValueError("Annotation/query mismatch")
    if any(not set(v)<=ids for v in annotations["relevance"].values()):
        raise ValueError("Unknown annotated trace")
    return corpus, annotations

def tokens(s): return set(re.findall(r"[a-z0-9]+",s.lower()))

def star_neighbors(corpus,anchor):
    result=set()
    for star in corpus["stars"]:
        if anchor in star["members"]:
            result.update(star["members"])
    result.discard(anchor)
    return result

def rank(corpus,query,architecture):
    if architecture not in {"A0","A1"}: raise ValueError("Unknown architecture")
    neighbors=star_neighbors(corpus,query["anchor"]) if architecture=="A1" else set()
    qt=tokens(query["text"]); rows=[]
    for item in corpus["traces"]:
        if item["id"]==query["anchor"]: continue
        lexical=len(qt & tokens(item["text"]))
        bonus=2 if item["id"] in neighbors else 0
        rows.append((-(lexical+bonus),item["id"],lexical,bonus))
    return sorted(rows)

def evaluate(k=4):
    corpus,ann=load(); out={"queries":[]}
    totals={a:{"precision":0,"recall":0,"linked_irrelevant":0} for a in ("A0","A1")}
    for q in corpus["queries"]:
        relevant=set(ann["relevance"][q["id"]]); neighbors=star_neighbors(corpus,q["anchor"])
        row={"query":q["id"],"relevant":sorted(relevant),"graph_neighbors":sorted(neighbors),"architectures":{}}
        for arch in ("A0","A1"):
            returned=[x[1] for x in rank(corpus,q,arch)[:k]]
            hits=len(relevant & set(returned))
            precision=hits/k; recall=hits/len(relevant)
            linked_bad=len((set(returned)&neighbors)-relevant) if arch=="A1" else 0
            row["architectures"][arch]={"retrieved":returned,"precision_at_4":precision,
                "recall_at_4":recall,"linked_irrelevant_retrieved":linked_bad}
            totals[arch]["precision"]+=precision; totals[arch]["recall"]+=recall
            totals[arch]["linked_irrelevant"]+=linked_bad
        out["queries"].append(row)
    n=len(corpus["queries"])
    out["summary"]={a:{"mean_precision_at_4":round(totals[a]["precision"]/n,4),
        "mean_recall_at_4":round(totals[a]["recall"]/n,4),
        "linked_irrelevant_retrieved":totals[a]["linked_irrelevant"]} for a in ("A0","A1")}
    out["interpretation_constraints"]=[
      "Relevance annotations are separate from graph membership.",
      "Graph memberships remain hand-seeded experimental inputs, not inferred links.",
      "Deliberate false-positive and missing graph relations test harm as well as utility.",
      "This benchmark does not establish real-world graph induction quality."]
    return out

if __name__=="__main__": print(json.dumps(evaluate(),indent=2,sort_keys=True))
