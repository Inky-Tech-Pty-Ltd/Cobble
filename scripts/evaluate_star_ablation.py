"""Ablate Star Credential representation while holding hypothesis membership constant.

This tests Cobble retrieval mechanics only. It does not determine which
representation has the correct VillageLink semantics, provenance, governance,
interchange, or publication properties.
"""
import json
from pathlib import Path
from evaluate_independent_benchmark import load, tokens

def membership_views(corpus):
    views={"star":{},"pairwise":{},"collection":{}}
    for star in corpus["stars"]:
        members=list(star["members"])
        for member in members:
            peers=set(members)-{member}
            views["star"].setdefault(member,set()).update(peers)
            views["collection"].setdefault(member,set()).update(peers)
        # Pairwise centre-to-member assertions can reconstruct co-membership
        # only when the shared centre/group identifier is retained.
        centre=star["centre"]
        for member in members:
            views["pairwise"].setdefault((centre,member),set()).add(member)
    reconstructed={}
    by_centre={}
    for star in corpus["stars"]:
        by_centre[star["centre"]]=set(star["members"])
    for centre,members in by_centre.items():
        for member in members:
            reconstructed.setdefault(member,set()).update(members-{member})
    views["pairwise_reconstructed"]=reconstructed
    return views

def rank_with_neighbors(corpus,query,neighbors,k=4):
    qt=tokens(query["text"]); rows=[]
    for item in corpus["traces"]:
        if item["id"]==query["anchor"]: continue
        lexical=len(qt & tokens(item["text"]))
        bonus=2 if item["id"] in neighbors else 0
        rows.append((-(lexical+bonus),item["id"]))
    return [x[1] for x in sorted(rows)[:k]]

def evaluate():
    corpus,annotations=load(); views=membership_views(corpus)
    result={"queries":[],"equivalence":{}}
    for q in corpus["queries"]:
        row={"query":q["id"],"retrieval":{}}
        for name in ("star","collection","pairwise_reconstructed"):
            neighbors=views[name].get(q["anchor"],set())
            row["retrieval"][name]=rank_with_neighbors(corpus,q,neighbors)
        result["queries"].append(row)
    for name in ("collection","pairwise_reconstructed"):
        result["equivalence"][name+"_matches_star"]=all(
          r["retrieval"][name]==r["retrieval"]["star"] for r in result["queries"])
    result["interpretation"]=[
      "For this Cobble ranking function, retrieval depends on recoverable co-membership, not StarCredential syntax.",
      "This does not show that a collection or pairwise representation is semantically equivalent for VillageLink publication or exchange.",
      "Pairwise reconstruction requires a retained shared-centre/group identity; bare unrelated edges are insufficient."
    ]
    return result

if __name__=="__main__": print(json.dumps(evaluate(),indent=2,sort_keys=True))
