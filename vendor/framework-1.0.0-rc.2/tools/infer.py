"""Generic inference over a loaded store (framework + one project). Used by the per-FDPS
checks and by the Demo page generator. No project identifiers are hard-coded here."""
EMAX_OPEN = 999
class Infer:
    def __init__(s, store):
        s.R = store["records"]; s.IDX = {r["id"]: r for r in s.R}
        s.REG = {e["id"]: e for e in store["register_entries"]}; s.PAR = {e["id"]: e.get("parent") for e in store["register_entries"]}
        s.STR = {e["id"] for e in store["register_entries"] if e["register"] == "SYS" and e.get("is_structural")}
        s.PRJ = next((r for r in s.R if r["type"] == "Project"), {})
        s.EMAX = s.PRJ.get("effectivity_max", 60)
        s.pages = {}
        for p in s.of("Hub Page"):
            if p.get("framework_node") and p.get("framework_node") != "ALL":
                cur = s.pages.get(p["framework_node"])
                if cur is None or (cur.get("hub") == "FW" and p.get("hub") != "FW"): s.pages[p["framework_node"]] = p  # project page overrides framework page
    def of(s, t): return [r for r in s.R if r["type"] == t]
    @staticmethod
    def lk(r, t): return [l["target"] for l in r.get("links", []) if l["link_type"] == t]
    def lab(s, i): return s.REG[i]["label"] if i in s.REG else s.IDX.get(i, {}).get("title", i)
    def members(s, f): return s.lk(f, "Contains")
    def pis(s, f): return [m for m in s.members(f) if m.startswith("PI")]
    def home(s, p): return s.lk(s.IDX[p], "Homed in")[0]
    def chain(s, sub): y = s.PAR[sub]; return [sub, y, s.PAR[y]]
    def systems(s, f): return sorted({s.PAR[s.home(p)] for p in s.pis(f)})
    def homes(s, f): return sorted({s.home(p) for p in s.pis(f)})
    def stations(s, f):
        out = set()
        for m in s.members(f): out |= set(s.lk(s.IDX[m], "Located at"))
        return sorted(out)
    def major_units(s, f): return sorted({s.PAR[b] for b in s.stations(f)})
    def is_structural(s, f): return s.PAR.get(f.get("lead_sub_system")) in s.STR
    def fdps_of(s, inst):
        return next((f["id"] for f in s.of("FDPS") if inst in s.members(f)), None)
    def interfaces(s, f):
        """{system: [routes]} with route (a) Sub-system page list, (b) Sub-structure page list, (c) Supports link; minus own Systems."""
        own = set(s.systems(f)); got = {}; ssf = s.is_structural(f)
        for p in s.pis(f):
            h = s.home(p); pg = s.pages.get(h, {})
            if s.PAR[h] not in s.STR or ssf:
                for y in pg.get("interfaces", []): got.setdefault(y, set()).add(("b" if s.PAR[h] in s.STR else "a") + ":" + h)
            for y in s.lk(s.IDX[p], "Supports"): got.setdefault(y, set()).add("c:" + p)
        for a in s.members(f):
            if a.startswith("AI"):
                for y in s.lk(s.IDX[a], "Supports"): got.setdefault(y, set()).add("c:" + a)
        return {k: sorted(v) for k, v in got.items() if k not in own}
    def unbroken(s, f): return sorted(set(s.interfaces(f)) - {b["system"] for b in f.get("interface_breaks", [])})
    def fdps_interfaces(s, f):
        """Cross-FDPS Secures links in either direction (1.6.6, 6C.24)."""
        out = []; mine = set(s.members(f))
        for o in s.of("FDPS"):
            if o["id"] == f["id"]: continue
            for m in s.members(o):
                for t in s.lk(s.IDX[m], "Secures"):
                    if t in mine: out.append({"fdps": o["id"], "fastener": m, "held": t, "direction": "in"})
            for m in sorted(mine):
                for t in s.lk(s.IDX[m], "Secures"):
                    if t in s.members(o): out.append({"fdps": o["id"], "fastener": m, "held": t, "direction": "out"})
        return out
    def team_page(s, f): return s.pages.get(s.PAR[f["owning_sub_team"]], {})
    def subteam_page(s, f): return s.pages.get(f["owning_sub_team"], {})
    def inherited(s, f):
        """{req_or_tsm_id: [bases]}: Requirements by System tree node or direct link; TSMs by Design Type, System or Discipline (OR)."""
        out = {}; pis = s.pis(f); mems = set(s.members(f))
        for r in s.of("Requirement"):
            b = []
            for node in s.lk(r, "Allocated to"):
                via = sorted(p for p in pis if node in s.chain(s.home(p)))
                if via: b.append({"basis": "Inherited via System tree node", "node": node, "via": via})
            for t in s.lk(r, "Satisfied by"):
                if t == f["id"] or t in mems: b.append({"basis": "Direct", "item": t})
            if b: out[r["id"]] = b
        defs = sorted({s.lk(s.IDX[m], "Instance of")[0] for m in s.members(f)} & {d["id"] for d in s.of("Part Definition")})
        disc = s.team_page(f).get("applicable_disciplines", [])
        for t in s.of("TSM"):
            b = []
            for g in s.lk(t, "Governs"):
                if g.startswith("VR-DTY"):
                    via = [d for d in defs if g in (s.IDX[d].get("design_type"), s.IDX[d].get("modification_design_type"))]
                    if via: b.append({"basis": "Inherited via Design Type", "design_type": g, "via": via})
                elif g.startswith("VR-SYS"):
                    via = sorted(p for p in pis if s.PAR[s.home(p)] == g)
                    if via: b.append({"basis": "Inherited via System", "system": g, "via": via})
                elif g in disc: b.append({"basis": "Inherited via Discipline", "discipline": g, "via": [s.team_page(f).get("id")]})
            if b: out[t["id"]] = b
        return out
    def statements(s, f): return [c for c in s.of("Compliance Statement") if c["fdps"] == f["id"]]
    def revisions(s, f): return sorted([r for r in s.of("FDPS Revision") if r["fdps"] == f["id"]], key=lambda r: r["effectivity"]["from"])
    def reviews(s, f):
        ids = {r["id"] for r in s.revisions(f)}
        return sorted([d for d in s.of("Design Review") if set(s.lk(d, "Covers")) & ids], key=lambda d: d["review_date"])
    def actions(s, f):
        ds = {d["id"] for d in s.reviews(f)}
        return [a for a in s.of("Action") if set(s.lk(a, "Raised at")) & ds or f["id"] in s.lk(a, "Tagged to")]
    def has_role(s, person, role, kind=None, ref=None):
        return any(a["person"] == person and a["role"] == role and (kind is None or a["area"]["kind"] == kind) and (ref is None or a["area"]["ref"] == ref) for a in s.of("Role Assignment"))
    def design_leads(s, node):
        return sorted({a["person"] for a in s.of("Role Assignment") if a["role"] == "Design Lead" and (a["area"]["ref"] == node or s.PAR.get(a["area"]["ref"]) == node)})
    def na_disciplines(s):
        return {t["payload"]["discipline"] for t in s.of("Tailoring Record") if t.get("action") == "mark Discipline not applicable" and isinstance(t.get("payload"), dict)}
    def present(s, inst, n): e = s.IDX[inst]["existence"]; return e["from"] <= n <= e["to"]
    def effective_revision(s, f, n):
        return next((r for r in s.revisions(f) if r["effectivity"]["from"] <= n <= r["effectivity"]["to"] and r.get("status") == "Released"), None)
