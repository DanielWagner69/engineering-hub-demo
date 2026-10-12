"""Checks for Requirements Prompt v24.6 / Data Schema v7.6 (project mode): EDRs and line items
(6B.1A, 6B.2, 6B.5, 6B.7, 6B.7A, 6C.11, 6C.13, 6C.15) and Users, access roles and permissions (5A, B.6)."""
from infer import Infer
MAY = {"Admin": None, "Design Lead": {"Design Lead"}, "Design Authority": {"Design Authority"}, "Engineer": {"Technical Authority for Design", "Technical Authority for Design (Design Licence Holder)", "Design Approver", "Discipline Lead"}, "Viewer": set()}
def run(store, cfg):
    I = Infer(store); res = []
    def chk(n, ok, d=""): res.append(("U", n, bool(ok), d))
    P = [r for r in store["records"] if r.get("hub") not in ("FW", None)]
    U = I.users(); PA = [a for a in I.of("Project Assignment") if a.get("status", "Active") == "Active"]
    pa = {a["user"]: a for a in PA}
    uid = {u["id"]: u for u in I.of("User")}
    # ---- users
    refs = [(r["id"], r.get("owner")) for r in P if r["type"] not in ("User",)] + [(r["id"], c) for r in P for c in r.get("contributors", [])]
    bad = [x for x in refs if x[1] not in U]
    chk("Every Owner and Contributor of a project record is a User (5A.1, 5A.7)", U and not bad, bad[:5])
    chk("Contributors are optional lists of Users and never repeat the Owner (5A.7)", all(isinstance(r.get("contributors", []), list) and r.get("owner") not in r.get("contributors", []) for r in P))
    dup = [u for u in uid if sum(1 for a in PA if a["user"] == u and a["project"] == I.PRJ.get("id")) > 1]
    chk("At most one active Project Assignment per User per project, each with one access role (5A.3)", not dup and all(a["user"] in uid and a["project"] == I.PRJ.get("id") for a in PA), dup[:5])
    admins = {a["user"] for a in PA if a["access_role"] == "Admin"} | {u["id"] for u in uid.values() if u.get("framework_admin")}
    chk("Every Project Assignment, Effectivity Restriction and Permission Override is set by an Admin on the project or a framework administrator (5A.8)",
        admins and all(a["assigned_by"] in admins for a in PA) and all(e["set_by"] in admins for e in I.of("Effectivity Restriction")) and all(o["approved_by"] in admins for o in I.of("Permission Override")))
    effs = {e["id"] for e in I.of("Effectivity")}; er = {}
    for e in I.of("Effectivity Restriction"): er.setdefault(e["project_assignment"], []).append(e)
    badr = [a["id"] for a in PA if (a["effectivity_access"] == "Restricted") != bool(er.get(a["id"]))] + [e["id"] for e in I.of("Effectivity Restriction") if not e["effectivity"] or not set(e["effectivity"]) <= effs]
    chk("Restricted access has at least one Effectivity Restriction of the project, and All has none (5A.4)", not badr, badr[:5])
    nopa = [h for h in U if U[h]["user_status"] == "Active" and U[h]["id"] not in pa and not U[h].get("framework_admin")]
    chk("Every active User has an active Project Assignment; suspended or departed Users have no active access (5A.1, 5A.3)", not nopa and all(U[h]["id"] not in pa or U[h]["user_status"] == "Active" for h in U), nopa[:5])
    owners = {r.get("owner") for r in P if r["type"] not in ("User", "Project Assignment", "Effectivity Restriction", "Permission Override")}
    vo = sorted(h for h in owners if h in U and pa.get(U[h]["id"], {}).get("access_role") in (None, "Viewer"))
    chk("Every Owner holds an active Project Assignment with edit permission (not Viewer) (5A.7, B.6)", not vo, vo[:5])
    ra = [(a["id"], a["person"], a["role"]) for a in I.of("Role Assignment") if a["status"] == "Active" and not (a["person"] in U and (lambda r: r == "Admin" or a["role"] in MAY.get(r, set()))(pa.get(U[a["person"]]["id"], {}).get("access_role")))]
    chk("Every authority role in the Role register is held with a matching access role: Design Lead, Design Authority, or Engineer for TA, Design Approver and Discipline Lead; Admin may hold any (5A.6)", not ra, ra[:5])
    po = [o["id"] for o in I.of("Permission Override") if o["effect"] not in ("Grant", "Deny") or not o.get("reason") or o["user"] not in uid]
    chk("Permission Overrides name a User, a single permission, Grant or Deny, a reason and the approving Admin (5A.5)", not po, po[:5])
    # ---- EDRs and line items
    D = {d["id"]: d for d in I.edrs()}
    np = [r["id"] for r in I.of("Requirement") if len([x for x in I.lk(r, "Part of") if x in D]) != 1]
    chk("Every Requirement line item is Part of exactly one EDR; each EDR has a Sub-system tag (6B.1A, 6B.2)", D and not np and all(d["sub_system_tags"] for d in D.values()), np[:5])
    chk("EDR codes unique within the project (6B.1A)", len({d["doc_code"] for d in D.values()}) == len(D))
    chk("No TSM is tagged to a Sub-system; TSMs reach Sub-systems through Design Types (6B.5)", not [t["id"] for t in I.of("TSM") if any(g.startswith("VR-SUB-") for g in I.lk(t, "Governs"))])
    bk = []; sp = []; cs = []; un = []
    for f in I.of("FDPS"):
        li = I.line_items(f); kept = {(x["item"], x["clause"]) for x in li if x["state"] == "Kept"}
        for x in li:
            r = x["review"]
            if not r: continue
            if r["state"] == "Broken":
                if not (r.get("reason") and r.get("approved_by")): bk.append(r["id"])
                elif x["kind"] == "EDR" and not (I.has_role(r["approved_by"], "Design Lead", ref=f["lead_sub_system"]) or I.has_role(r["approved_by"], "Design Lead", ref=I.PAR.get(f["lead_sub_system"]))): bk.append(r["id"])
                elif x["kind"] == "TSM" and not I.has_role(r["approved_by"], "Design Authority"): bk.append(r["id"])
            if r["state"] == "Superseded (auto)" and (not r.get("superseded_by") or (x["kind"] == "EDR" and x["defined"])): sp.append(r["id"])
            if r["state"] == "Kept" and x["kind"] == "TSM" and not any(x["clause"] in [q["clause"] for q in c.get("statements_claimed", [])] for c in I.statements(f) if c["requirement"] == x["item"]): sp.append(r["id"])
        for c in I.statements(f):
            if c["requirement"].startswith("REQ") and (c["requirement"], None) not in kept and c["position"] != "Not applicable": cs.append(c["id"])
        m = I.maturity(f)
        if any(r.get("status") == "Released" for r in I.revisions(f)) and (m["unreviewed"] or m["pending_bulk"]): un.append((f["id"], m))
    chk("Every Broken line item has a reason and the right approver: Design Lead of the FDPS lead Sub-system (or its System) for EDR line items, a Design Authority for TSM statements (6B.7, 6C.13)", not bk, bk[:5])
    chk("Superseded (auto) only where the level has defined links that do not reach the line item, with those links recorded; Kept TSM statements are claimed with parts (6B.7A P1 to P3)", not sp, sp[:5])
    chk("Compliance Statements are claimed only for Kept EDR line items (6B.11)", not cs, cs[:5])
    chk("No unreviewed line item and no pending TSM bulk confirmation on any FDPS with a released revision (Stage C entry and release gate, 6C.11, 6C.15)", not un, un[:3])
    tc = [c["id"] for c in I.of("TSM Supersession Confirmation") if not I.has_role(c.get("confirmed_by"), "Design Authority")]
    chk("TSM supersessions are bulk-confirmed by a Design Authority (6B.7A P5)", not tc, tc[:5])
    return res
