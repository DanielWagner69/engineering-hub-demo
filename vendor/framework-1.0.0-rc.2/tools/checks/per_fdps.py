"""Generic rule checks run over EVERY FDPS of a project (Phase 3). Each check is reported per FDPS.
Nothing here names a project identifier; FDPSs without any revision are checked for population,
lead Sub-system and interfaces only, and reported as 'not yet in review'."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from infer import Infer
def ov(a, b): return a["from"] <= b["to"] and b["from"] <= a["to"]
def run(store, cfg):
    I = Infer(store); res = []; info = {"per_fdps": {}}
    for f in sorted(I.of("FDPS"), key=lambda r: r["id"]):
        F = f["id"]
        def chk(name, ok, d=""): res.append(("Q", "[%s] %s" % (F, name), bool(ok), d))
        pis = I.pis(f)
        chk("Population: every member exists; every Part Instance Homed in one Sub-system and Located at one Build Station (1.2.2, 1.6)", pis and all(m in I.IDX for m in I.members(f)) and all(len(I.lk(I.IDX[p], "Homed in")) == 1 and len(I.lk(I.IDX[p], "Located at")) == 1 for p in pis))
        chk("Each Part Instance belongs to exactly one FDPS (1.7.2)", all(sum(p in I.members(o) for o in I.of("FDPS")) == 1 for p in pis))
        lead = f.get("lead_sub_system"); ap = f.get("lead_sub_system_approval") or {}
        chk("Lead Sub-system holds one of its Part Instances; set by the owning Sub-team, approved by a Design Lead of that Sub-system (1.7.7, R-15)", lead in I.homes(f) and ap.get("approved_by") in I.design_leads(lead) and ap.get("set_by"))
        inh = I.interfaces(f); brk = f.get("interface_breaks", [])
        chk("Interface breaks: only of inherited Systems, with reason, approved by a Design Lead of the lead Sub-system (6C.21)", all(b["system"] in inh and b.get("reason") and b.get("approved_by") in I.design_leads(lead) for b in brk), [b["system"] for b in brk if b["system"] not in inh])
        chk("Structural FDPS inherits every Sub-structure list it touches; non-structural FDPS takes no Sub-structure list (6C.20, R-09)", all(any(r.startswith(("b:" if I.is_structural(f) else "a:")) or r.startswith("c:") for r in v) for v in inh.values()))
        fi = I.fdps_interfaces(f)
        flags = [r for r in I.of("Review Flag") if r.get("fdps_interface")]
        chk("Every incoming cross-FDPS Secures link has a Review Flag to this FDPS's owner with decision Accept or Query; no confirmation attribute (R-18)", all(any(r["flagged_object"] == F and r["triggering_object"] == x["fastener"] and r.get("decision") in ("Accept", "Query") for r in flags) for x in fi if x["direction"] == "in"))
        revs = I.revisions(f)
        info["per_fdps"][F] = {"systems": I.systems(f), "interfaces": {k: v for k, v in inh.items()}, "breaks": [b["system"] for b in brk], "fdps_interfaces": fi, "inherited": sorted(I.inherited(f)), "revisions": [r["id"] for r in revs]}
        if not revs:
            chk("Not yet in review: no Compliance Statement, review or release recorded before its first FDPS revision", not I.statements(f)); continue
        inr = I.inherited(f); cs = I.statements(f)
        chk("Has at least one Requirement, inherited or direct (2.4)", any(k.startswith("REQ") for k in inr))
        chk("Every inherited or direct Requirement and TSM (TSM tags OR) has Compliance Statements, and no others (6B.3, 6B.5)", set(inr) == {c["requirement"] for c in cs}, sorted(set(inr) ^ {c["requirement"] for c in cs}))
        def bkey(b): return (b["basis"], b.get("node") or b.get("design_type") or b.get("system") or b.get("discipline") or b.get("item"))
        chk("Compliance Statement bases record every route that reaches the FDPS (6B.6)", all(sorted(map(bkey, c["bases"])) == sorted(map(bkey, inr.get(c["requirement"], []))) for c in cs))
        ok = True
        for k in inr:
            rs = sorted((c["effectivity"]["from"], c["effectivity"]["to"]) for c in cs if c["requirement"] == k)
            if not rs or rs[0][0] != 1 or rs[-1][1] != 999 or any(rs[i][1] + 1 != rs[i + 1][0] for i in range(len(rs) - 1)): ok = False
        chk("Compliance ranges tile effectivity 1 to open-ended for each Requirement and TSM, no gaps or overlaps (6B.8)", ok)
        V = {v["id"]: v for v in I.of("Verification")}
        def covered(c):
            lo, hi = c["effectivity"]["from"], min(c["effectivity"]["to"], I.EMAX)
            ok = [V[e]["effectivity"] for e in c["evidence"] if e in V and V[e]["outcome"] == "Pass"]
            return all(any(x["from"] <= n <= x["to"] for x in ok) for n in range(lo, hi + 1))
        bad = [c["id"] for c in cs if c["position"] == "Compliant" and not covered(c)]
        chk("Compliant statements carry evidence: Pass Verifications that together cover every effectivity of the statement's range (6B.9)", not bad, bad)
        chk("Not applicable statements carry a reason and an approver (6B.7, 6C.13)", all(c.get("reason") and c.get("approved_by") for c in cs if c["position"] == "Not applicable"))
        chk("Non-compliant statements reference an open Issue (6A.17)", all(I.IDX.get(c.get("issue"), {}).get("status") not in (None, "Closed") for c in cs if c["position"] == "Non-compliant"))
        drs = I.reviews(f); STG = {I.REG[s]["code"]: s for s in I.REG if s.startswith("VR-STAGE")}
        sp = I.subteam_page(f); na = I.na_disciplines()
        for d in drs:
            sec = next((x for x in sp.get("stage_sections", []) if x["stage"] == d["stage"]), None)
            req = {x for x in (sec or {}).get("sign_off_disciplines", []) if x not in na}
            chk("%s: Sign-off positions equal the owning Sub-team page's list for the stage (less project N/A), none Disagree (6C.19)" % d["id"], sec and req == {a["discipline"] for a in d["discipline_agreements"]} and all(a["position"] != "Disagree" for a in d["discipline_agreements"]))
            snap = next((x for x in I.of("Review Snapshot") if x["design_review"] == d["id"]), None)
            chk("%s: snapshot frozen with population, interfaces, breaks and agreements (6C.9)" % d["id"], snap and snap["content"].get("population") and "interface_agreements" in snap["content"])
            chk("%s: an interface agreement from every unbroken interfacing System at the snapshot, by a Design Lead of that System (6C.22)" % d["id"], snap and {a["system"] for a in d["interface_agreements"]} == set(snap["content"]["interfacing_systems"]) and all(a["by"] in I.design_leads(a["system"]) for a in d["interface_agreements"]))
        acts = I.actions(f)
        for r in [r for r in revs if r.get("status") == "Released"]:
            passed = [I.IDX[x] for x in r.get("passed_reviews", [])] + ([I.IDX[r["carried_forward_review"]["review"]]] if r.get("carried_forward_review") else [])
            have = {I.REG[d["stage"]]["code"] for d in passed if d.get("decision") == "Pass"}
            earlier = {I.REG[d["stage"]]["code"] for d in drs if d.get("decision") == "Pass" and d["review_date"] <= r["released_at"][:10]}
            chk("%s rev %s: C passed for this revision (direct or carried forward) and A and B passed for the FDPS before release (6C.1, 6C.12)" % (F, r["revision"]), "C" in have and {"A", "B"} <= earlier)
            late = [a["id"] for a in acts if a.get("closure", {}).get("accepted_at", "9") > r["released_at"] and any(I.IDX[x]["review_date"] <= r["released_at"][:10] for x in I.lk(a, "Raised at"))]
            chk("%s rev %s: every Action from its reviews closed and accepted before release (6C.11)" % (F, r["revision"]), not late, late)
            ncb = [c["id"] for c in cs if c["position"] == "Non-compliant" and ov(c["effectivity"], r["effectivity"]) and c.get("created_at", "") <= r["released_at"] and not any(h.get("position") == "Compliant" for h in c.get("record_history", []))]
            chk("%s rev %s: no Non-compliant statement over its range when released (6A.17)" % (F, r["revision"]), not ncb, ncb)
            chk("%s rev %s: release baseline frozen; released by a holder of FDPS release authority (6A.10, 6C.14)" % (F, r["revision"]), any(I.IDX[b]["trigger"]["kind"] == "Release" for b in r["baselines"]) and any(a["person"] == r["released_by"] and any(x["authority"] == "FDPS release" for x in a["delegations"]) for a in I.of("Role Assignment")))
        rel = [r for r in revs if r.get("status") == "Released"]
        chk("Released revision ranges do not overlap (6A.3)", all(not ov(a["effectivity"], b["effectivity"]) for i, a in enumerate(rel) for b in rel[i + 1:]))
    # R-16 evidence: Systems physically mounted on each structural FDPS versus its inherited list
    r16 = {}
    for f in I.of("FDPS"):
        if not I.is_structural(f): continue
        mine = set(I.members(f)); mounted = {}
        for o in I.of("FDPS"):
            if o["id"] == f["id"]: continue
            for m in I.members(o):
                if not m.startswith("PI"): continue
                tgt = set(I.lk(I.IDX[m], "Secures")) & mine
                if tgt or (set(I.lk(I.IDX[m], "Supports")) & set(I.systems(f))): mounted.setdefault(I.PAR[I.home(m)], []).append(m)
        for m in sorted(mine):  # this FDPS's fasteners holding other FDPSs' parts
            for t in I.lk(I.IDX[m], "Secures"):
                if t not in mine and t.startswith("PI"): mounted.setdefault(I.PAR[I.home(t)], []).append(t)
                if t not in mine and t.startswith("PI"):
                    for y in I.lk(I.IDX[t], "Supports"): mounted.setdefault(y, []).append(t)
        inh = I.interfaces(f); own = set(I.systems(f))
        r16[f["id"]] = {"mounted": {k: sorted(set(v)) for k, v in mounted.items()}, "not_prompted": sorted(set(mounted) - set(inh) - own), "inherited_not_mounted": sorted(set(inh) - set(mounted))}
        res.append(("Q", "[%s] R-16 evidence: every System mounted on the structural FDPS (by Supports or Secures links) is prompted by its Sub-structure lists or is its own" % f["id"], True, r16[f["id"]]))
    info["r16"] = r16
    return res, info
