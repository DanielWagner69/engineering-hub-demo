"""v1.1-demo data (Requirements Prompt v24.6 / Data Schema v7.6), all fictional:
EDRs (Requirement Documents) with Part of links; Sub-system applicable Design Types; Line-item Reviews
(Kept, Broken, Superseded (auto)) and TSM Supersession Confirmations for every inherited line item;
Users, Project Assignments, Effectivity Restrictions and Permission Overrides; Contributors.
Deterministic: run from the repo root after the framework tools are vendored. Re-running rewrites the same files."""
import json, os, sys, copy
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = os.path.join(ROOT, "data", "project-d"); REC = os.path.join(D, "records")
FW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "vendor", "framework-1.0.0-rc.3")
sys.path.insert(0, os.path.join(FW, "tools")); import load
from infer import Infer
def rd(t):
    p = os.path.join(REC, t + ".json"); return json.load(open(p)) if os.path.exists(p) else []
def wr(t, rs): json.dump(rs, open(os.path.join(REC, t + ".json"), "w"), indent=1, ensure_ascii=False)
PRJ = "PRJ-D-0000001"; NOW = "2026-10-12T14:00:00Z"
def base(i, typ, title, owner, status, at=NOW):
    return {"id": i, "type": typ, "schema_version": "7.6", "title": title, "status": status, "owner": owner, "hub": PRJ, "created_at": at, "created_by": owner, "modified_at": at, "modified_by": owner,
            "record_version": 1, "origin": {"kind": "Human"}, "verification_status": "Verified", "verified_by": owner, "verified_at": at, "access_marking": "VR-ACCESS-0001"}
# ---- EDRs
EDR = [("EDR-D-0000001", "EDR-FUE", "Fuel System Engineering Design Requirements", ["VR-SUB-0031", "VR-SUB-0032", "VR-SUB-0033", "VR-SUB-0034", "VR-SUB-0035", "VR-SUB-0036"], ["REQ-D-0000140", "REQ-D-0000141", "REQ-D-0000142", "REQ-D-0000145"], "user:j.ward"),
       ("EDR-D-0000002", "EDR-PP", "Propulsion and Power Engineering Design Requirements", ["VR-SUB-0032", "VR-SUB-0012"], ["REQ-D-0000146"], "user:s.price"),
       ("EDR-D-0000003", "EDR-STR", "Primary Structure Engineering Design Requirements", ["VR-SUB-0001"], ["REQ-D-0000147", "REQ-D-0000148"], "user:g.burns"),
       ("EDR-D-0000004", "EDR-SST", "Secondary Structure Engineering Design Requirements", ["VR-SUB-0005"], ["REQ-D-0000143"], "user:y.hart")]
docs = []
for i, code, title, tags, reqs, own in EDR:
    d = base(i, "Requirement Document", title, own, "Released", "2025-11-20T09:00:00Z")
    d.update(doc_kind="EDR", doc_code=code, issue=1, sub_system_tags=tags, product_scope=["VR-SCOPE-0001"], issue_changes=[{"issue": 1, "changed": reqs}], links=[{"link_type": "Tagged to", "target": t} for t in tags])
    docs.append(d)
wr("Requirement_Document", docs)
part = {r: d["id"] for d, e in zip(docs, EDR) for r in e[4]}
Q = rd("Requirement")
for r in Q:
    r["links"] = [l for l in r["links"] if l["link_type"] != "Part of"] + [{"link_type": "Part of", "target": part[r["id"]]}]
    r["line_item_revision"] = 1
wr("Requirement", Q)
for t in (T := rd("TSM")):
    for c in t["statements"]: c["revision"] = 1
wr("TSM", T)
SDT = {"VR-SUB-0032": ["VR-DTY-0009", "VR-DTY-0011", "VR-DTY-0012", "VR-DTY-0002"], "VR-SUB-0031": ["VR-DTY-0009", "VR-DTY-0002", "VR-DTY-0003"], "VR-SUB-0005": ["VR-DTY-0002", "VR-DTY-0003", "VR-DTY-0012"], "VR-SUB-0001": ["VR-DTY-0002", "VR-DTY-0003", "VR-DTY-0012"]}
HP = rd("Hub_Page")
for p in HP:
    if p.get("framework_node") in SDT: p["applicable_design_types"] = SDT[p["framework_node"]]
wr("Hub_Page", HP)
# ---- Users (fictional)
people = json.load(open(os.path.join(D, "project.json")))["people"]
for a in rd("Role_Assignment"):
    if a["person"] not in people: people[a["person"]] = "%s. %s, %s" % (a["person"][5].upper(), a["person"].split(".")[1].capitalize(), a["role"])
extra = {"user:hub.admin": "Demo Admin, Hub administrator (fictional)", "user:m.castell": "M. Castell, Fuel designer (restricted to effectivities 1 to 2)", "user:a.brooks": "A. Brooks, supplier engineer (viewer, suspended)"}
U = []; n = 0; hid = {}
for h, desc in list(people.items()) + list(extra.items()):
    if h == "user:framework_owner": continue
    n += 1; i = "USR-D-%07d" % n; hid[h] = i; nm = desc.split(",")[0]
    u = base(i, "User", nm, "user:hub.admin", "Active"); u.update(display_name=nm, email="%s@example.invalid" % h.split(":")[1], handle=h, user_status="Suspended" if h == "user:a.brooks" else "Active", framework_admin=False, role_note=desc.split(", ", 1)[1] if ", " in desc else "")
    U.append(u)
wr("User", U)
RA = rd("Role_Assignment"); roles = {}
for a in RA: roles.setdefault(a["person"], set()).add(a["role"])
def access(h):
    if h == "user:hub.admin": return "Admin"
    if h == "user:a.brooks": return "Viewer"
    r = roles.get(h, set())
    if "Design Lead" in r: return "Design Lead"
    if "Design Authority" in r: return "Design Authority"
    return "Engineer"
PA = []; ER = []; k = 0
for u in U:
    if u["user_status"] != "Active": continue
    k += 1; i = "PA-D-%07d" % k; restricted = u["handle"] in ("user:m.castell",)
    a = base(i, "Project Assignment", "%s on Project D: %s" % (u["display_name"], access(u["handle"])), "user:hub.admin", "Active", "2026-09-01T09:00:00Z")
    a.update(user=u["id"], project=PRJ, access_role=access(u["handle"]), effectivity_access="Restricted" if restricted else "All", from_date="2026-09-01", assigned_by=hid["user:hub.admin"])
    PA.append(a)
    if restricted:
        e = base("ER-D-0000001", "Effectivity Restriction", "M. Castell: effectivities 1 and 2", "user:hub.admin", "Active", "2026-09-01T09:00:00Z")
        e.update(project_assignment=i, effectivity=["EFF-D-0000001", "EFF-D-0000002"], set_by=hid["user:hub.admin"], set_at="2026-09-01T09:00:00Z"); ER.append(e)
wr("Project_Assignment", PA); wr("Effectivity_Restriction", ER)
po = base("PO-D-0000001", "Permission Override", "M. Castell: grant Approve on Lesson Learned", "user:hub.admin", "Active")
po.update(user=hid["user:m.castell"], project=PRJ, permission={"data_type": "Lesson Learned", "action": "Approve"}, effect="Grant", reason="Covers Lessons Learned review while the Fuel lead is on leave (demo)", expires_on="2026-11-30", approved_by=hid["user:hub.admin"])
po2 = base("PO-D-0000002", "Permission Override", "A. Novak: deny Edit on FDPS", "user:hub.admin", "Active")
po2.update(user=hid["user:a.novak"], project=PRJ, permission={"data_type": "FDPS", "action": "Edit"}, effect="Deny", reason="Stress reviewer keeps FDPS data read-only (demo)", approved_by=hid["user:hub.admin"])
wr("Permission_Override", [po, po2])
# ---- Contributors
CON = {"FD-D-0000017": ["user:p.hale", "user:m.castell"], "FD-D-0000009": ["user:h.grant"], "ISS-D-0000058": ["user:a.novak"], "LL-D-0000031": ["user:p.hale"]}
for f in os.listdir(REC):
    rs = json.load(open(os.path.join(REC, f))); ch = False
    for r in rs:
        if r["id"] in CON: r["contributors"] = [c for c in CON[r["id"]] if c != r.get("owner")]; ch = True
    if ch: json.dump(rs, open(os.path.join(REC, f), "w"), indent=1, ensure_ascii=False)
# ---- Line-item Reviews from the inheritance (Kept where claimed, Broken with approver, Superseded (auto) otherwise)
wr("Line-item_Review", []); wr("TSM_Supersession_Confirmation", [])
st = load.load(os.path.join(FW, [x for x in os.listdir(FW) if x.endswith(".json") and x.startswith("framework-")][0]), D); I = Infer(st)
LIR = []; TSC = []; m = 0
for f in sorted(I.of("FDPS"), key=lambda f: f["id"]):
    cs = I.statements(f); dl = sorted(I.design_leads(f["lead_sub_system"]) or ["user:s.price"])[0]
    pend = {}
    for x in I.line_items(f):
        m += 1; i = "LIR-D-%07d" % m; who = f["owner"]
        r = base(i, "Line-item Review", "", who, "Current", "2026-05-08T09:00:00Z")
        r.update(fdps=f["id"], line_item={"requirement": x["item"]} if x["kind"] == "EDR" else {"tsm": x["item"], "clause": x["clause"]}, line_item_revision=1, bases=x["route"], author=who, links=[{"link_type": "Reviews line item", "target": x["item"]}])
        if x["kind"] == "EDR":
            c = [c for c in cs if c["requirement"] == x["item"]]
            if c and all(y["position"] == "Not applicable" for y in c):
                r.update(state="Broken", reason=c[0].get("reason", "Not applicable to this FDPS"), approved_by=dl, approved_at="2026-05-08T09:00:00Z")
            elif c: r["state"] = "Kept"
            else: r.update(state="Superseded (auto)", superseded_by=["Allocated to (defined links at this level)"])
            name = I.IDX[x["item"]]["req_number"]
        else:
            c = [c for c in cs if c["requirement"] == x["item"]]
            claimed = {s["clause"] for y in c for s in y.get("statements_claimed", [])}
            if claimed and x["clause"] in claimed: r["state"] = "Kept"
            elif c and all(y["position"] == "Not applicable" for y in c):
                da = next(a["person"] for a in I.of("Role Assignment") if a["role"] == "Design Authority")
                r.update(state="Broken", reason=c[0].get("reason", "Statement not applicable"), approved_by=c[0].get("approved_by") if I.has_role(c[0].get("approved_by"), "Design Authority") else da, approved_at="2026-05-08T09:00:00Z")
            else:
                r.update(state="Superseded (auto)", superseded_by=[y["id"] for y in c if y.get("statements_claimed")] or ["Part Design Type links (defined at part level)"]); pend.setdefault(x["item"], []).append(i)
            name = "%s %s" % (I.IDX[x["item"]]["manual_code"], x["clause"])
        r["title"] = "%s: %s %s" % (f["fdps_number"], name, r["state"]); LIR.append(r)
    for t, ids in sorted(pend.items()):
        gv = I.lk(I.IDX[t], "Governs"); da = next((a["person"] for a in I.of("Role Assignment") if a["role"] == "Design Authority" and a["area"]["ref"] in gv), None) or next(a["person"] for a in I.of("Role Assignment") if a["role"] == "Design Authority")
        c = base("TSC-D-%07d" % (len(TSC) + 1), "TSM Supersession Confirmation", "%s: %s superseded statements confirmed" % (f["fdps_number"], I.IDX[t]["manual_code"]), da, "Confirmed", "2026-05-09T09:00:00Z")
        c.update(tsm=t, fdps=f["id"], reviews=ids, confirmed_by=da, confirmed_at="2026-05-09T09:00:00Z"); TSC.append(c)
        for r in LIR:
            if r["id"] in ids: r["bulk_confirmation"] = c["id"]
wr("Line-item_Review", LIR); wr("TSM_Supersession_Confirmation", TSC)
from collections import Counter
print("EDRs", len(docs), "Users", len(U), "PAs", len(PA), "LIRs", len(LIR), Counter(r["state"] for r in LIR), "TSCs", len(TSC))
