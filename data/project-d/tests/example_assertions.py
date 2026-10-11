"""Project D example assertions: values stated in Worked Example v4 (run on the Demo only).
The inference outputs must be the same as those recorded when WE4 was validated."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
def _norm(x):
    if isinstance(x, dict): return {k: _norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return sorted((_norm(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True, default=str))
    return x
def run(store, cfg, info):
    exp = json.load(open(os.path.join(HERE, "expected_info_we4.json"))); res = []
    got = json.loads(json.dumps(info, default=str))
    diff = [k for k in exp if _norm(exp[k]) != _norm(got.get(k))]
    res.append(("X", "Inference outputs equal those recorded for Worked Example v4 (interfaces, configuration, compliance bases, fasteners, release checks)", not diff, diff))
    n = cfg["expect"]["interfacing_systems"]["FD-D-0000017"]
    res.append(("X", "FD-D-0000017 inherits %d interfacing Systems after breaks (WE4 section 5)" % n, got["iface"][0] == n, got["iface"]))
    R = store["records"]; I = {r["id"]: r for r in R}
    nc = [r for r in R if r["type"] == "Compliance Statement" and r["position"] == "Non-compliant" and r["effectivity"]["from"] <= 2]
    ok = bool(nc) and all(I.get(c.get("issue"), {}).get("status", "Closed") != "Closed" for c in nc)
    for c in nc:
        for fr in [r for r in R if r["type"] == "FDPS Revision" and r["fdps"] == c["fdps"]]:
            if fr["effectivity"]["from"] <= c["effectivity"]["to"] and fr["effectivity"]["to"] >= c["effectivity"]["from"] and fr.get("released_at", "") >= c["modified_at"]: ok = False
    res.append(("X", "Effectivities 1 to 2 shown Non-compliant with the Issue open and no release over that range since (decision 9)", ok, [c["id"] for c in nc]))
    return res
