"""Checks added in the rebuild: register integrity, considerations, late decisions
R-15 (lead Sub-system set and approved) and R-18 (cross-FDPS Secures flags: Accept or Query,
no confirmation). run(store, cfg, project_mode) returns results [(section, name, ok, detail)]."""
import json, re
VR = re.compile(r"\bVR-[A-Z]+-\d{4}\b")
def run(store, cfg, project_mode=True):
    R = store["records"]; IDX = {r["id"]: r for r in R}; E = store["register_entries"]; REG = {e["id"]: e for e in E}
    res = []
    def chk(sec, name, ok, detail=""): res.append((sec, name, bool(ok), detail))
    def of(t): return [r for r in R if r["type"] == t]
    def lk(r, t): return [l["target"] for l in r.get("links", []) if l["link_type"] == t]
    byreg = {}
    for e in E: byreg.setdefault(e["register"], []).append(e)
    # ---- H. registers and considerations
    allids = [r["id"] for r in R] + [e["id"] for e in E]
    chk("H", "Identifiers unique across records and register entries, never reused (2A.4)", len(allids) == len(set(allids)), sorted({i for i in allids if allids.count(i) > 1})[:5])
    unres = sorted(set(VR.findall(json.dumps(R) + json.dumps(E))) - set(REG))
    chk("H", "Every register reference resolves to a register entry (2B.1, 2B.9)", not unres, unres[:10])
    dup = [(r, c) for r, es in byreg.items() for c in {e["code"] for e in es} if sum(1 for e in es if e["code"] == c) > 1 and r not in ("SUB",)]
    subdup = [(e["parent"], e["code"]) for e in byreg.get("SUB", []) if sum(1 for x in byreg["SUB"] if x["parent"] == e["parent"] and x["code"] == e["code"]) > 1]
    chk("H", "Register codes unique within each register (Sub-system codes within their System) (schema 2.1)", not dup and not subdup, (dup + subdup)[:5])
    badpar = [e["id"] for e in E if e.get("parent") and e["parent"] not in REG]
    chk("H", "Register parents resolve (System to System Group, Sub-system to System, Build Station to Major Unit, Sub-team to Team) (1.4)", not badpar, badpar[:5])
    syss = byreg.get("SYS", []); subs = byreg.get("SUB", [])
    chk("H", "Every System has exactly one General Sub-system (catch-all) (2B.11)", syss and all(sum(1 for s in subs if s["parent"] == y["id"] and s.get("is_catch_all")) == 1 for y in syss))
    mus = byreg.get("MU", []); bss = byreg.get("BS", [])
    chk("H", "Every Major Unit has exactly one Bench Build Station; Final Assembly is the Major Unit catch-all (2C.12, 2C.11)",
        mus and all(sum(1 for b in bss if b["parent"] == m["id"] and b.get("is_bench")) == 1 for m in mus) and sum(1 for m in mus if m.get("is_catch_all")) == 1)
    chk("H", "Structural flag set on every System; structural Systems are the Airframe System Group (2B.11, 0.4)",
        all("is_structural" in y for y in syss) and {y["id"] for y in syss if y["is_structural"]} == {y["id"] for y in syss if REG.get(y["parent"], {}).get("code") == "AF"})
    lcs = sorted(byreg.get("LCS", []), key=lambda e: e["sequence_no"])
    chk("H", "Lifecycle Stage register: 11 stages in order, stages 4 to 6 in current scope; review stages A, B, C aligned to 4, 5, 6 (2B.13, 6C.1)",
        [e["sequence_no"] for e in lcs] == list(range(1, 12)) and [e["sequence_no"] for e in lcs if e["in_current_scope"]] == [4, 5, 6]
        and [REG[s["lifecycle_stage"]]["sequence_no"] for s in sorted(byreg.get("STAGE", []), key=lambda x: x["code"])] == [4, 5, 6])
    disc = byreg.get("DISC", [])
    chk("H", "Discipline register: 26 entries, one list with no duplicate labels, each with a Discipline type (2B.14, B.2)",
        len(disc) == 26 and len({d["label"] for d in disc}) == 26 and all(REG.get(d.get("discipline_type"), {}).get("register") == "DISC_TYPE" for d in disc))
    DCs = of("Design Consideration"); stages = sorted(e["id"] for e in byreg.get("STAGE", []))
    ok = sorted(d["discipline"] for d in DCs) == sorted(d["id"] for d in disc)
    ids = [i["item_id"] for d in DCs for c in d["checklists"] for i in c["items"]]
    for d in DCs:
        if sorted(c["stage"] for c in d["checklists"]) != stages or any(len(c["items"]) < 1 for c in d["checklists"]): ok = False
    chk("H", "Exactly one Design Consideration per Discipline, each with checklist items for review stages A, B and C (3.22, 4.2, 4.4)", ok)
    chk("H", "Checklist item identifiers unique across all Design Considerations (4.4)", len(ids) == len(set(ids)), sorted({i for i in ids if ids.count(i) > 1})[:5])
    st = {i.get("item_status") for d in DCs for c in d["checklists"] for i in c["items"]}
    chk("H", "Starter checklist items carry a review state (Draft until reviewed with the framework owner) (decision 7)", st <= {"Draft", "Reviewed"} and None not in st)
    if not project_mode: return res
    # ---- I. late decisions R-15 and R-18
    RA = of("Role Assignment"); FDs = of("FDPS")
    def dl(p, sub, date): return any(a["person"] == p and a["role"] == "Design Lead" and a["area"]["kind"] == "Sub-system" and a["area"]["ref"] == sub and a["from_date"] <= date[:10] and (not a.get("to_date") or a["to_date"] >= date[:10]) for a in RA)
    def in_team(p, f, date):
        dst = f["owning_sub_team"]; dt = REG[dst]["parent"]
        return p == f["owner"] or any(a["person"] == p and a["area"]["ref"] in (dst, dt) and a["from_date"] <= date[:10] for a in RA)
    bad = []
    for f in FDs:
        a = f.get("lead_sub_system_approval") or {}
        if not (a.get("set_by") and a.get("approved_by") and a.get("set_at") and a.get("approved_at")): bad.append((f["id"], "missing")); continue
        if not in_team(a["set_by"], f, a["set_at"]): bad.append((f["id"], "set_by not in owning Sub-team"))
        if not dl(a["approved_by"], f["lead_sub_system"], a["approved_at"]): bad.append((f["id"], "approver is not a Design Lead of the lead Sub-system"))
        if a["approved_at"] < a["set_at"]: bad.append((f["id"], "approved before set"))
    chk("I", "R-15: each FDPS's lead Sub-system set by its owning Design Sub-team and approved by a Design Lead of that Sub-system at the date (1.7.7, 6C.14)", FDs and not bad, bad)
    CRs = of("Change Record"); badc = []
    for f in FDs:
        hist = f.get("record_history", [])
        leads = [h.get("lead_sub_system", None) for h in hist if "lead_sub_system" in h]
        if not any(l != f["lead_sub_system"] for l in leads): continue
        cr = IDX.get((f.get("lead_sub_system_approval") or {}).get("change_record"))
        if not cr or cr["type"] != "Change Record" or "VR-CHG-0011" not in cr.get("change_types", []) or f["id"] not in [x["fdps"] for x in cr.get("fdps_assessments", [])]:
            badc.append((f["id"], "lead changed without a Lead Sub-system change Change Record")); continue
        for b in f.get("interface_breaks", []):
            if b["approved_at"] < cr["created_at"] and not (b.get("reconfirm_required") or (b.get("reconfirmed_at", "") >= cr["created_at"])): badc.append((f["id"], b["system"], "break not flagged for re-confirmation"))
    chk("I", "R-15: a change of lead Sub-system is a Change Record (Lead Sub-system change) that re-runs interface inheritance and flags existing breaks for re-confirmation (1.7.7, 6C.21)", not badc, badc)
    mem = {m: f["id"] for f in FDs for m in lk(f, "Contains")}
    cross = [(p["id"], s) for p in of("Part Instance") for s in lk(p, "Secures") if p["id"] in mem and s in mem and mem[p["id"]] != mem[s]]
    RFs = of("Review Flag"); badf = []
    for pid, s in cross:
        other = mem[s]; fl = [r for r in RFs if r["flagged_object"] == other and r["triggering_object"] == pid and r.get("fdps_interface")]
        if not fl: badf.append((pid, "no FDPS-interface flag to the other FDPS")); continue
        for r in fl:
            if r["decision"] != "Open" and r.get("decided_by") != IDX[other]["owner"]: badf.append((r["id"], "decided by someone other than the other FDPS's owner"))
    chk("I", "R-18: each cross-FDPS Secures link raises a Review Flag to the owner of the other FDPS, decided by that owner (1.6.6, 6C.24)", cross and not badf, badf)
    IF = [r for r in RFs if r.get("fdps_interface")]
    badd = [r["id"] for r in IF if r["decision"] not in ("Open", "Accept", "Query") or (r["decision"] == "Query" and r["status"] not in ("Open", "Query"))]
    badd += [r["id"] for r in RFs if not r.get("fdps_interface") and r["decision"] in ("Accept", "Query")]
    chk("I", "R-18: FDPS-interface flags are decided Accept or Query (a Query stays open); other flags do not use Accept or Query (2I.3)", IF and not badd, badd)
    conf = [(p["id"], l) for p in of("Part Instance") for l in p.get("links", []) if l["link_type"] == "Secures" and set(l.get("attributes", {})) & {"confirmation_required", "confirmed_by", "pending"}]
    blk = [f["id"] for f in of("FDPS Revision") if any(q in json.dumps(f.get("gate_confirmation", {})) for q in [r["id"] for r in IF if r["decision"] == "Query"])]
    chk("I", "R-18: a cross-FDPS Secures link needs no confirmation, and a Query does not block the link or release (6C.24)", not conf and not blk, conf + blk)
    return res
