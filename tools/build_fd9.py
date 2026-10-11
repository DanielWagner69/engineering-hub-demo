"""Phase 3: promote FD-D-0000009 (frames 14 to 15A, fictional) to a full structural FDPS:
frames 15 and 15A, team and Sub-team pages, Requirements, Compliance Statements, Verifications,
reviews A to C with snapshots and agreements, checklist responses, an Action, rev A release and
baselines (closes R-19). Idempotent: removes what it added before writing. Run from the repo root."""
import json, os, glob, hashlib, copy
D = "data/project-d/records"; TAG = "fd9_phase3"
def load(t):
    p = os.path.join(D, t.replace(" ", "_") + ".json")
    return json.load(open(p)) if os.path.exists(p) else []
def save(t, rs): json.dump(rs, open(os.path.join(D, t.replace(" ", "_") + ".json"), "w"), indent=1, ensure_ascii=False)
ALL = {}
for f in glob.glob(os.path.join(D, "*.json")):
    t = os.path.basename(f)[:-5].replace("_", " "); ALL[t] = [r for r in json.load(open(f)) if r.get("_gen") != TAG and not r.get("x_phase3")]
def base(i, t, title, owner, at, status="Approved", **kw):
    r = {"id": i, "type": t, "schema_version": "6.0", "title": title, "status": status, "owner": owner, "hub": "PRJ-D-0000001", "created_at": at, "created_by": owner,
         "modified_at": at, "modified_by": owner, "record_version": 1, "origin": {"kind": "Human"}, "verification_status": "Verified", "verified_by": owner, "verified_at": at,
         "access_marking": "VR-ACCESS-0001", "x_phase3": True}
    r.update(kw); ALL.setdefault(t, []).append(r); return r
E1 = {"effectivity_type": "VR-EFFTYPE-0001", "from": 1, "to": 999}
idx = {r["id"]: r for v in ALL.values() for r in v}
# ---- frames 15 and 15A
for n, (fr, stem) in enumerate([("Frame 15", "D5012003"), ("Frame 15A", "D5012004")]):
    pd = copy.deepcopy(idx["PD-D-0000120"]); pd.update({"id": "PD-D-012%d" % (1 + n) if False else "PD-D-%07d" % (121 + n), "title": fr + ", centre fuselage", "part_number": stem + "-001", "stem": stem, "x_phase3": True})
    pd["number_proposal"] = dict(pd["number_proposal"], proposed_number=stem + "-001"); ALL["Part Definition"].append(pd)
    base("PR-D-%07d" % (221 + n), "Part Revision", stem + "-001 rev A", "user:h.grant", "2025-11-20T09:00:00Z", "Released", part_definition=pd["id"], revision="A", issuing_master="VR-MASTER-0001",
         external_ref="PLM-%s-001-A" % stem, released_by="user:a.quinn", released_at="2025-12-10T09:00:00Z", links=[], mass={"value": 3.1 + n * 0.4, "unit": "kg"})
    base("PI-D-%07d" % (5004 + n), "Part Instance", fr + ", centre fuselage", "user:h.grant", "2025-11-25T09:00:00Z", "Active", position_name=fr + ", centre fuselage", existence=E1,
         links=[{"link_type": "Instance of", "target": pd["id"]}, {"link_type": "Located at", "target": "VR-BS-0005"}, {"link_type": "Homed in", "target": "VR-SUB-0001"}])
    base("IRL-D-%07d" % (9204 + n), "Instance-Revision Link", "PI-D-%07d to %s-001 rev A" % (5004 + n, stem), "user:e.dunn", "2025-11-25T09:00:00Z", "Open-ended",
         instance="PI-D-%07d" % (5004 + n), revision="PR-D-%07d" % (221 + n), effectivity=E1, set_by_master="VR-MASTER-0001")
fd = idx["FD-D-0000009"]
fd["title"] = "Centre fuselage frames 14 to 15A installation"; fd["status"] = "Released"; fd.pop("context_note", None)
fd["links"] = [l for l in fd["links"] if l["target"] not in ("PI-D-0005004", "PI-D-0005005")] + [{"link_type": "Contains", "target": "PI-D-0005004"}, {"link_type": "Contains", "target": "PI-D-0005005"}]
fd["record_version"] = 2; fd["modified_at"] = "2026-03-17T09:00:00Z"; fd.setdefault("record_history", [{"record_version": 1, "modified_at": "2025-11-20T09:00:00Z", "status": "Open"}])
# ---- roles: Structures Design Authority with release delegation; Design Leads for Systems without one
base("RA-D-0000033", "Role Assignment", "user:a.quinn: Design Authority, VR-DT-0001", "user:s.price", "2025-11-03T09:00:00Z", "Active", person="user:a.quinn", role="Design Authority",
     area={"kind": "Design Team", "ref": "VR-DT-0001"}, delegated_by="user:s.price", from_date="2025-11-03", delegations=[{"authority": "FDPS release", "to": "user:a.quinn", "from_date": "2025-11-03"}])
RA = [r for r in ALL["Role Assignment"]]
fw = json.load(open(sorted(glob.glob("vendor/framework-*/framework-*.json"))[-1])); PAR = {e["id"]: e.get("parent") for e in fw["register_entries"]}
def dl(sysid): return next((r["person"] for r in RA if r["role"] == "Design Lead" and (r["area"]["ref"] == sysid or PAR.get(r["area"]["ref"]) == sysid)), None)
newdl = {"VR-SYS-0003": "user:c.ash", "VR-SYS-0008": "user:m.dale", "VR-SYS-0009": "user:t.ross", "VR-SYS-0015": "user:i.webb"}
k = 34
for s, p in newdl.items():
    if not dl(s):
        RA.append(base("RA-D-%07d" % k, "Role Assignment", "%s: Design Lead, %s" % (p, s), "user:s.price", "2025-11-03T09:00:00Z", "Active", person=p, role="Design Lead", area={"kind": "System", "ref": s}, delegated_by="user:s.price", from_date="2025-11-03", delegations=[])); k += 1
# ---- team and Sub-team pages (Project D tailoring)
base("PG-D-0000301", "Hub Page", "Design Team: Structures", "user:a.quinn", "2025-11-10T09:00:00Z", "Published", page_type="VR-PAGETYPE-0004", framework_node="VR-DT-0001", template="TPL-0004",
     body={"blocks": [{"text": "Design Team: Structures (Project D tailoring of the framework template, 6C.6)."}]}, lifecycle_stage=["ALL"], discipline=["ALL"], last_reviewed_at="2025-11-10",
     applicable_design_types=["VR-DTY-0002", "VR-DTY-0003", "VR-DTY-0004", "VR-DTY-0005", "VR-DTY-0012"], applicable_disciplines=["VR-DISC-0022"])
SO = {"VR-STAGE-0001": ["VR-DISC-0006", "VR-DISC-0019", "VR-DISC-0022", "VR-DISC-0025", "VR-DISC-0003"],
      "VR-STAGE-0002": ["VR-DISC-0006", "VR-DISC-0019", "VR-DISC-0022", "VR-DISC-0015", "VR-DISC-0014", "VR-DISC-0025", "VR-DISC-0003"],
      "VR-STAGE-0003": ["VR-DISC-0006", "VR-DISC-0019", "VR-DISC-0022", "VR-DISC-0015", "VR-DISC-0014", "VR-DISC-0018", "VR-DISC-0021", "VR-DISC-0005", "VR-DISC-0003", "VR-DISC-0013", "VR-DISC-0025"]}
CKI = {"VR-STAGE-0001": [("VR-DISC-0022", "SA-A-01"), ("VR-DISC-0023", "SLI-A-01"), ("VR-DISC-0025", "WGT-A-01")],
       "VR-STAGE-0002": [("VR-DISC-0022", "SA-B-01"), ("VR-DISC-0015", "MP-B-01"), ("VR-DISC-0001", "AIT-B-01")],
       "VR-STAGE-0003": [("VR-DISC-0022", "SA-C-01"), ("VR-DISC-0014", "MFG-C-01"), ("VR-DISC-0021", "SPS-C-01")]}
dcs = {d["discipline"]: d for d in fw["records"] if d["type"] == "Design Consideration"}
items = {i["item_id"] for d in dcs.values() for s in d["checklists"] for i in s["items"]}
for st in CKI: CKI[st] = [(dd, it) for dd, it in CKI[st] if it in items and dcs[dd]["discipline"] == dd]
base("PG-D-0000311", "Hub Page", "Design Sub-team: Centre Structure", "user:a.quinn", "2025-11-10T09:00:00Z", "Published", page_type="VR-PAGETYPE-0005", framework_node="VR-DST-0002", template="TPL-0005",
     body={"blocks": [{"text": "Design Sub-team: Centre Structure (Project D tailoring of the framework template, 6C.6)."}]}, lifecycle_stage=["VR-LCS-0004", "VR-LCS-0005", "VR-LCS-0006"], discipline=["ALL"], last_reviewed_at="2025-11-10",
     stage_sections=[{"stage": s, "checklist_items": [{"discipline": dd, "item_id": it} for dd, it in CKI[s]], "sign_off_disciplines": SO[s], "type_specific_entry_criteria": []} for s in SO])
# ---- Requirements
def req(i, num, title, stmt, node, crit, disc):
    base(i, "Requirement", title, "user:j.ward", "2025-11-20T09:00:00Z", "Accepted", req_number=num, statement=stmt, level="VR-REQLVL-0003", criteria=crit, product_scope=["VR-SCOPE-0001"], lifecycle_stage=["ALL"],
         discipline=[disc], acceptance={"state": "Accepted", "accepted_by": "user:o.fry", "accepted_at": "2025-11-20T09:00:00Z"}, links=[{"link_type": "Allocated to", "target": node}])
req("REQ-D-0000147", "D-STR-FRM-002", "Frame ultimate strength", "Fuselage frames shall sustain ultimate load (1.5 x limit load) without failure.", "VR-SUB-0001", [{"quantity_name": "reserve_factor_ultimate", "comparator": ">=", "limit": {"value": 1.0, "unit": "1"}}], "VR-DISC-0022")
req("REQ-D-0000148", "D-STR-GEN-007", "Primary structure fatigue life", "Primary structure shall achieve a fatigue life of not less than 3 times the design service goal without crack initiation.", "VR-SYS-0001", [{"quantity_name": "fatigue_scatter_life", "comparator": ">=", "limit": {"value": 3, "unit": "1"}}], "VR-DISC-0022")
# ---- Verifications
PRS = ["PR-D-0000220", "PR-D-0000221", "PR-D-0000222"]
def ver(i, title, meth, summ, res, outcome, basis, links, disc="VR-DISC-0022", doc=None, at="2026-02-24T09:00:00Z"):
    base(i, "Verification", title, "user:a.novak", at, "Approved", method=meth, summary=summ, results=res, outcome=outcome, basis_revisions=basis, effectivity=E1, discipline=disc,
         lifecycle_stage="VR-LCS-0006", document={"source_ref": doc or i.replace("VER", "CALC"), "issue": 1}, links=links)
ver("VER-D-0000320", "Frames 14 to 15A static strength analysis", "VR-VMETH-0003", "Finite element analysis of frames 14, 15 and 15A at ultimate load cases.", [{"quantity_name": "reserve_factor_ultimate", "value": {"value": 1.22, "unit": "1"}, "margin": {"value": 0.22, "unit": "1"}}], "Pass", PRS, [{"link_type": "Demonstrates", "target": "REQ-D-0000147"}], doc="CALC-D-0201")
ver("VER-D-0000321", "Frames 14 to 15A fatigue analysis", "VR-VMETH-0003", "Fatigue analysis at frame cut-outs and fastener holes, including the bracket and clamp boss holes.", [{"quantity_name": "fatigue_scatter_life", "value": {"value": 4.1, "unit": "1"}, "margin": {"value": 1.1, "unit": "1"}}], "Pass", PRS, [{"link_type": "Demonstrates", "target": "REQ-D-0000148"}], doc="CALC-D-0202")
ver("VER-D-0000322", "Frames 14 to 15A design inspection against TSM-MET", "VR-VMETH-0008", "Inspection of machined frame definitions for internal corner radii.", [], "Pass", PRS, [{"link_type": "Demonstrates", "target": "TSM-D-0000063"}], doc="INSP-D-0203")
ver("VER-D-0000323", "Frame 14 bracket fastener installation inspection against TSM-STD", "VR-VMETH-0008", "Bolt protrusion on the valve bracket fasteners at frame 14.", [], "Pass", ["PR-D-0000211", "PR-D-0000212"], [{"link_type": "Demonstrates", "target": "TSM-D-0000066"}], disc="VR-DISC-0021", doc="INSP-D-0204")
# ---- Compliance Statements (bases are what the Hub infers; generator below fills them)
import sys; sys.path.insert(0, sorted(glob.glob("vendor/framework-*/tools"))[-1])
from infer import Infer
def store():
    recs = [r for v in ALL.values() for r in v]
    pj = json.load(open("data/project-d/register_entries.json")) if os.path.exists("data/project-d/register_entries.json") else []
    pj = pj["entries"] if isinstance(pj, dict) else pj
    return {"records": recs + [r for r in fw["records"]], "register_entries": fw["register_entries"] + pj}
I = Infer(store()); inh = I.inherited(idx["FD-D-0000009"] if False else next(r for r in ALL["FDPS"] if r["id"] == "FD-D-0000009"))
pos = {"REQ-D-0000143": ("Not applicable", [], {"reason": "Only the frame 14 valve bracket fasteners of this FDPS are homed in Brackets and Supports; the bracket strength Requirement is claimed by the FDPS that owns the bracket (D2822001-801).", "approved_by": "user:y.hart", "approved_at": "2026-02-24T09:00:00Z"}),
       "REQ-D-0000147": ("Compliant", ["VER-D-0000320"], {}), "REQ-D-0000148": ("Compliant", ["VER-D-0000321"], {}),
       "TSM-D-0000063": ("Compliant", ["VER-D-0000322"], {"statements_claimed": [{"clause": "2.4.1"}]}), "TSM-D-0000066": ("Compliant", ["VER-D-0000323"], {"statements_claimed": [{"clause": "3.4"}]})}
assert set(inh) == set(pos), sorted(inh)
CS = []
for n, k in enumerate(sorted(inh)):
    p, ev, extra = pos[k]; num = (idx.get(k) or next(r for r in ALL["Requirement"] if r["id"] == k)).get("req_number") or idx[k].get("manual_code")
    CS.append(base("CS-D-%07d" % (1220 + n), "Compliance Statement", "D5012001-801, %s, effectivity 1 to 999 (open)" % num, "user:h.grant", "2026-02-24T09:00:00Z", "Approved", fdps="FD-D-0000009", requirement=k,
                   effectivity=E1, bases=inh[k], position=p, evidence=ev, **extra))
# ---- reviews, snapshots, baselines, checklist responses, action, release
pop = [{"instance": p + "@1", "irl": [i + "@1"]} for p, i in [("PI-D-0005001", "IRL-D-0009201"), ("PI-D-0005002", "IRL-D-0009202"), ("PI-D-0005003", "IRL-D-0009203"), ("PI-D-0005004", "IRL-D-0009204"), ("PI-D-0005005", "IRL-D-0009205")]]
F9 = next(r for r in ALL["FDPS"] if r["id"] == "FD-D-0000009"); ifs = I.unbroken(F9); brk = [b["system"] for b in F9["interface_breaks"]]
fdi = [{"fdps": x["fdps"], "fastener": x["fastener"], "held": x["held"]} for x in I.fdps_interfaces(F9)]
REASON = {"VR-SYS-0010": "Fuel feed clamps bolt to the frame 15A boss; the frame 14 valve bracket is held by this FDPS's fasteners (FDPS interface with D2822001-801)",
          "VR-SYS-0012": "Twin-pipe bracket at frame 15 carries a hydraulic pipe"}
DLP = {s: next(r["person"] for r in RA if r["role"] == "Design Lead" and (r["area"]["ref"] == s or PAR.get(r["area"]["ref"]) == s)) for s in ifs}
DLD = {r["area"]["ref"]: r["person"] for r in RA if r["role"] == "Discipline Lead"}
dates = {"VR-STAGE-0001": ("2026-01-06", "2025-12-22"), "VR-STAGE-0002": ("2026-02-03", "2026-01-20"), "VR-STAGE-0003": ("2026-03-03", "2026-02-17")}
names = {"VR-STAGE-0001": "A", "VR-STAGE-0002": "B", "VR-STAGE-0003": "C"}
bls = []; drs = []
for n, st in enumerate(SO):
    day, iss = dates[st]; at = day + "T09:00:00Z"; dr = "DR-D-%07d" % (5 + n); rs = "RS-D-%07d" % (5 + n); bl = "BL-D-%07d" % (8 + n)
    ia = [{"system": s, "position": "Agree", "reasons": REASON.get(s, "No item of this System is attached to frames 14 to 15A in the current population; kept on the Sub-structure list (over-inclusion accepted, R-09)"), "conditions": [], "by": DLP[s], "at": at} for s in ifs]
    da = [{"discipline": d, "position": "Agree", "reasons": "", "conditions": [], "by": DLD[d], "at": at} for d in SO[st]]
    content = {"population": pop, "interfacing_systems": ifs, "interface_breaks": brk, "fdps_interfaces": fdi, "compliance_statements": [c["id"] + "@1" for c in CS] if st == "VR-STAGE-0003" else [], "interface_agreements": ia, "fdps_revisions": ["FR-D-0000036"]}
    h = "sha256:" + hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]
    drs.append(base(dr, "Design Review", "Scheme review %s, centre fuselage frames 14 to 15A (D5012001-801)" % names[st], "user:a.quinn", iss + "T09:00:00Z", "Closed", stage=st, review_date=day, material_issued_at=iss, chair="user:s.price",
         attendees=[{"person": "user:h.grant", "represents": "Centre Structure Sub-team", "role": "Designer"}, {"person": "user:a.quinn", "represents": "Structures Design Team", "role": "Design Authority"}, {"person": "user:s.price", "represents": "Project", "role": "Technical Authority for Design (chair)"}, {"person": "user:g.burns", "represents": "Primary Structure", "role": "Design Lead"}]
         + [{"person": DLD[d], "represents": I.lab(d), "role": "Discipline Lead"} for d in SO[st]] + [{"person": DLP[s], "represents": I.lab(s), "role": "Design Lead"} for s in ifs],
         introduction={"scope": "FDPS D5012001-801 (FR-D-0000036)"}, entry_check=[{"criterion": c, "met": True} for c in {"A": ["Allocated Requirements and interfacing Systems identified", "Concept layout in the integrated model"], "B": ["Preliminary sizing complete", "Applicable TSMs identified"], "C": ["Full detail design", "Compliance stated against every inherited and linked Requirement and TSM", "All interfaces agreed"]}[names[st]]],
         known_risks=[], minutes="Stage %s accepted.%s" % (names[st], " Action ACT-D-0000106 raised on the frame 15A boss edge distance." if names[st] == "B" else ""), discipline_agreements=da, interface_agreements=ia, decision="Pass", decision_by="user:s.price", decision_at=at,
         content={"generated_from": ["PG-D-0000311#stage-%s" % names[st], "FD-D-0000009", "inferred Requirements, TSMs and interfacing Systems of the FDPS"]}, links=[{"link_type": "Covers", "target": "FR-D-0000036"}]))
    base(rs, "Review Snapshot", "Snapshot for " + dr, "user:e.dunn", at, "Frozen", design_review=dr, taken_at=at, content=content, content_hash=h, baseline=bl, links=[{"link_type": "Records", "target": dr}])
    bls.append(base(bl, "Baseline", "D5012001-801 rev A baseline %d" % (n + 1), "user:e.dunn", at, "Frozen", fdps_revision="FR-D-0000036", sequence_no=n + 1, trigger={"kind": "Review snapshot", "ref": rs}, effectivity=E1, frozen_at=at,
         content={k: v for k, v in content.items() if k in ("population", "interfacing_systems", "interface_breaks", "fdps_interfaces", "compliance_statements")}, content_hash=h))
    for m, (dd, it) in enumerate(CKI[st]):
        base("CK-D-%07d" % (21 + 3 * n + m), "Checklist Response", "%s Yes" % it, "user:h.grant", (day if False else iss) + "T09:00:00Z", "Submitted", fdps_revision="FR-D-0000036", stage=st, consideration=dcs[dd]["id"], item_id=it, response="Yes", responder="user:h.grant")
base("ACT-D-0000106", "Action", "Confirm frame 15A boss edge distance for the mid-span clamp bolt", "user:a.novak", "2026-02-03T09:00:00Z", "Closed", description="Confirm edge distance and hole fatigue allowance at the frame 15A boss that takes the fuel feed mid-span clamp bolt.",
     raised_by="user:a.novak", due_date="2026-02-24", closure={"evidence": "VER-D-0000321 covers the boss hole (fatigue scatter life 4.1).", "closed_by": "user:h.grant", "closed_at": "2026-02-24T09:00:00Z", "accepted_by": "user:a.novak", "accepted_at": "2026-02-25T09:00:00Z"},
     links=[{"link_type": "Raised at", "target": "DR-D-0000006"}, {"link_type": "Tagged to", "target": "FD-D-0000009"}], source={"kind": "Review", "ref": "DR-D-0000006"})
rel = "2026-03-17T09:00:00Z"
content = dict(bls[-1]["content"]); h = "sha256:" + hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]
bls.append(base("BL-D-0000011", "Baseline", "D5012001-801 rev A baseline 4", "user:e.dunn", rel, "Frozen", fdps_revision="FR-D-0000036", sequence_no=4, trigger={"kind": "Release", "ref": "REL-D-FR36-A"}, effectivity=E1, frozen_at=rel, content=content, content_hash=h))
base("FR-D-0000036", "FDPS Revision", "D5012001-801 rev A", "user:a.quinn", "2025-12-01T09:00:00Z", "Released", fdps="FD-D-0000009", revision="A", population=pop, effectivity=E1, passed_reviews=[d["id"] for d in drs], baselines=[b["id"] for b in bls],
     release_assessment={"assessed_by": "user:a.quinn", "at": "2026-03-16T09:00:00Z", "against_snapshot": "RS-D-0000007", "change_records": [], "substantial": False, "rationale": "No change since RS-D-0000007."},
     gate_confirmation={"confirmed_by": "Hub", "at": rel, "open_actions": [], "non_compliant_statements": []}, gate_attempts=[], released_at=rel, released_by="user:a.quinn", links=[])
for t, rs in ALL.items(): save(t, rs)
print("FD-D-0000009 built: inherited", sorted(inh), "interfacing", ifs)
