"""Demo Production Hub generator (plan 3.2, Phase 3). Builds every framework page from the pinned
bundle with the project's tailoring applied, adds production data to tree pages, FDPS pages,
record registers (record detail inside the register; no page per Part Instance), reports,
the tailoring register and framework feedback, then runs the site checks.
Usage: build_demo.py --framework <bundle.json> --project data/project-d --out docs [--repo .] [--old ids.json]"""
import argparse, html, json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import validate, build_site
from build_site import Site, slug, E
from infer import Infer
FW_URL = "https://danielwagner69.github.io/engineering-hub/"
TYPES = [("FDPS", "fdps-register"), ("FDPS Revision", "fdps-revisions"), ("Part Definition", "part-definitions"), ("Part Revision", "part-revisions"), ("Part Instance", "part-instances"),
 ("Instance-Revision Link", "instance-revision-links"), ("Assembly Definition", "assembly-definitions"), ("Assembly Revision", "assembly-revisions"), ("Assembly Instance", "assembly-instances"),
 ("Requirement", "requirements"), ("TSM", "tsms"), ("Compliance Statement", "compliance-statements"), ("Verification", "verifications"), ("Issue", "issues"), ("Lesson Learned", "lessons-learned"),
 ("Design Review", "design-reviews"), ("Review Snapshot", "review-snapshots"), ("Checklist Response", "checklist-responses"), ("Action", "actions"), ("Risk", "risks"), ("Change Record", "change-records"),
 ("Baseline", "baselines"), ("Review Flag", "review-flags"), ("Role Assignment", "role-register"), ("Authority Register Entry", "authority-register"), ("Production Link", "production-links"),
 ("Finish Specification", "finish-specifications"), ("Parameter", "parameters"), ("Parameter Iteration", "parameter-iterations"), ("Effectivity", "effectivities"), ("Tailoring Record", "tailoring-records"),
 ("Requirement Document", "edr-register"), ("Line-item Review", "line-item-reviews"), ("TSM Supersession Confirmation", "tsm-supersession-confirmations"), ("User", "user-register"), ("Project Assignment", "project-assignments"),
 ("Effectivity Restriction", "effectivity-restrictions"), ("Permission Override", "permission-overrides")]
STC = {"Kept": "ok", "Broken": "bad", "Superseded (auto)": "mid", "Inherited, not reviewed": "bad", "Direct": "ok"}
def rng(e): return "%d to %s" % (e["from"], "open" if e["to"] >= 999 else e["to"])
class Demo(Site):
    def __init__(s, st, out, inf):
        super().__init__(st, out); s.I = inf; s.P = inf.PRJ
        s.PR = [r for r in s.R if r.get("hub") not in ("FW", None) and r["type"] != "Hub Page" or (r["type"] == "Hub Page" and r.get("hub") != "FW")]
    NAV = [("Project", [("fdps/", "FDPSs"), ("edrs/", "EDRs"), ("tsms/", "TSMs"), ("users/", "People"), ("admin/users/", "Admin: users and access"), ("records/", "Record registers"), ("reports/coverage/", "Coverage report"), ("reports/release-gate/", "Release gate"), ("reports/open-flags/", "Review Flags"), ("tailoring/", "Tailoring"), ("feedback/", "Framework gaps")])] + Site.NAV
    def page_of(s, node):
        c = [p for p in s.R if p["type"] == "Hub Page" and p.get("framework_node") == node]
        return sorted(c, key=lambda p: p.get("hub") == "FW")[0]
    def rl(s, frm, i, text=None):
        """Link to a record: FDPS page, or its row in the record register."""
        if i is None: return ""
        if isinstance(i, str) and i.startswith("user:"): return s.ul(frm, i, text)
        base = i.split("@")[0]; r = s.I.IDX.get(base)
        if r is None: return s.link(frm, i, text) if i in s.url else E(text or i)
        t = text or i
        if r["type"] in ("FDPS", "Requirement Document", "TSM") and base in s.url: return '<a href="%s">%s</a>' % (s.rel(frm, s.url[base]), E(t))
        if r["type"] == "User": return s.ul(frm, r["handle"], text)
        reg = dict(TYPES).get(r["type"])
        if r.get("hub") == "FW" or not reg: return s.link(frm, base, t) if base in s.url else E(t)
        return '<a href="%s#%s">%s</a>' % (s.rel(frm, "records/%s/" % reg), E(base), E(t))
    def ul(s, frm, h, text=None):
        u = s.I.users().get(h); t = text or (u["display_name"] if u else h)
        return '<a href="%s">%s</a>' % (s.rel(frm, s.url[h]), E(t)) if h in s.url else E(t)
    def plan(s):
        super().plan()
        for f in s.I.of("FDPS"): s.url[f["id"]] = "fdps/%s/" % slug(f["fdps_number"])
        for d in s.I.edrs(): s.url[d["id"]] = "edrs/%s/" % slug(d["doc_code"])
        for t in s.I.of("TSM"): s.url[t["id"]] = "tsms/%s/" % slug(t["manual_code"])
        for u in s.I.of("User"): s.url[u["handle"]] = "users/%s/" % slug(u["handle"].split(":", 1)[1])
    # ---- v8 Sub-system pages with production data (5.21 to 5.30)
    def filter_opts(s):
        o = super().filter_opts(); effs = sorted(s.I.of("Effectivity"), key=lambda e: e["number"])
        o[1] = ("eff", "Effectivity", [("%d-%d" % (e["number"], e["number"]), "Aircraft %d (%s)" % (e["number"], e.get("serial", ""))) for e in effs] + [("%d-999" % (effs[-1]["number"] + 1), "Aircraft %d onward (future)" % (effs[-1]["number"] + 1))] if effs else [])
        return o
    def sub_fdps(s, sub): return sorted({s.I.fdps_of(p["id"]) for p in s.I.of("Part Instance") if s.I.lk(p, "Homed in") == [sub["id"]]} - {None})
    def sub_owner(s, sub, path):
        dl = s.I.design_leads(sub["id"])
        return ", ".join(s.ul(path, h) for h in dl) if dl else "No Design Lead assigned yet (Role register)"
    def sub_team(s, sub, path):
        ts = sorted({s.I.IDX[f]["owning_sub_team"] for f in s.sub_fdps(sub)})
        return ", ".join(s.link(path, t) for t in ts) if ts else "None yet (no FDPS)"
    def sub_meta(s, sub):
        dl = s.I.design_leads(sub["id"]); return {"owner": ", ".join(dl) if dl else "Design Lead (none assigned)"}
    def sub_groups(s, sub, sys_, path, fw_body):
        I = s.I; R = s.rl; L = s.link; F = [I.IDX[x] for x in s.sub_fdps(sub)]
        rngs = lambda e: "%d-%d" % (e["from"], e["to"])
        def dtys(f): return sorted({(I.IDX.get((I.lk(I.IDX[m], "Instance of") or [""])[0]) or {}).get("design_type") for m in I.members(f)} - {None})
        rows = ""
        for f in F:
            rv = I.revisions(f); e = (min(r["effectivity"]["from"] for r in rv), max(r["effectivity"]["to"] for r in rv)) if rv else None
            nc = s.nc_ranges(f); m = I.maturity(f)
            rows += "<li data-row%s data-dty='%s'>%s %s%s%s<br><small>Built at: %s · line items reviewed %d of %d</small></li>" % (" data-eff='%d-%d'" % e if e else "", " ".join(dtys(f)), R(path, f["id"], "%s %s" % (f["fdps_number"], f["title"])), "<span class='chip %s'>%s</span>" % ("ok" if f["status"] in ("Released",) else "", E(f["status"])),
                "".join("<span class='chip bad'>Release blocked eff. %s</span>" % rng(c["effectivity"]) for c in nc), "", ", ".join(L(path, b) for b in I.stations(f)), m["reviewed"], m["total"])
        fd = s.cat("fdps", "FDPSs", ("<ul class=rows>%s</ul><p class=nf>Level principle: Part Instances are listed on each FDPS page, not here (5.21). <a href='%s'>All FDPSs</a></p>" % (rows, s.rel(path, "fdps/"))) if F else "<p class=empty>No FDPS of {PROJ} has a Part Instance homed in this %s yet.</p>" % E(sub["label"]), len(F))
        ed = I.edrs_for_sub(sub["id"])
        er = "".join("<li class=doc data-row data-disc='%s'>%s <span class=chip>Issue %d</span><br><small>%s · %d line items · tagged to %d Sub-systems</small></li>" % (" ".join(sorted({x for q in I.edr_items(d) for x in q.get("discipline", [])})), R(path, d["id"], "%s %s" % (d["doc_code"], d["title"])), d["issue"], E(d["status"]), len(I.edr_items(d)), len(d["sub_system_tags"])) for d in ed)
        ts = I.tsms_for_sub(sub["id"])
        tr = "".join("<li class=doc data-row data-dty='%s' data-disc='%s'>%s <span class=chip>Issue %d</span><br><small>%s · %d statements</small></li>" % (" ".join(g for g in I.lk(t, "Governs") if g.startswith("VR-DTY")) or "ALL", " ".join(g for g in I.lk(t, "Governs") if g.startswith("VR-DISC")) or "ALL", R(path, t["id"], "%s %s" % (t["manual_code"], t["title"])), t["issue"], ("via Design Type " + ", ".join(L(path, x, I.lab(x).split(" (")[0]) for x in via)) if via else "via System tag " + L(path, sys_["id"]), len(t["statements"])) for t, via in ts)
        dts = I.sub_dtys(sub["id"])
        req = [s.cat("edrs", "EDRs", ("<ul class=rows>%s</ul>" % er) if ed else "<p class=empty>No EDR is tagged to this %s.</p>" % E(sub["label"]), len(ed)),
               s.cat("tsms", "TSMs", (("<p class=small>Applicable Design Types: %s (route Sub-system &gt; Design Type &gt; TSM, 6B.5).</p>" % ", ".join(L(path, x, I.lab(x).split(" (")[0]) for x in dts)) if dts else "") + (("<ul class=rows>%s</ul>" % tr) if ts else "<p class=empty>No TSM reaches this %s.</p>" % E(sub["label"])), len(ts))]
        cs = [c for f in F for c in I.statements(f)]
        crow = ""
        for f in F:
            li = I.line_items(f)
            for d in sorted({x["doc"] for x in li}):
                xs = [x for x in li if x["doc"] == d]; cc = [c for c in cs if c["fdps"] == f["id"] and (c["requirement"] == d or I.IDX[c["requirement"]].get("type") == "Requirement" and I.edr_of(c["requirement"]) == d)]
                pos = {}
                for c in cc: pos[c["position"]] = pos.get(c["position"], 0) + 1
                crow += "<tr data-row><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (R(path, d, I.IDX[d].get("doc_code") or I.IDX[d].get("manual_code")), R(path, f["id"], f["fdps_number"]), " ".join("<span class='chip %s'>%d %s</span>" % (STC.get(k, ""), n, E(k)) for k, n in sorted({x["state"]: sum(1 for y in xs if y["state"] == x["state"]) for x in xs}.items())), " ".join("<span class='chip %s'>%d %s</span>" % ("ok" if k == "Compliant" else ("bad" if k == "Non-compliant" else ""), n, E(k)) for k, n in sorted(pos.items())) or "none")
        ncs = [c for c in cs if c["position"] == "Non-compliant"]
        ncl = "".join("<li class=nc data-row data-eff='%s'>%s %s <span class='chip bad'>Non-compliant eff. %s</span> %s</li>" % (rngs(c["effectivity"]), R(path, c["id"]), (lambda d: R(path, d, "in " + (I.IDX[d].get("doc_code") or I.IDX[d].get("manual_code"))))(I.edr_of(c["requirement"]) if c["requirement"].startswith("REQ") else c["requirement"]), rng(c["effectivity"]), ("Issue " + R(path, c["issue"])) if c.get("issue") else "") for c in ncs)
        vs = sorted({v for c in cs for v in c["evidence"]})
        vrow = "".join("<li data-row%s>%s %s <small>%s</small></li>" % ((" data-eff='%s'" % rngs(I.IDX[v]["effectivity"])) if isinstance(I.IDX[v].get("effectivity"), dict) else "", R(path, v), E(I.IDX[v]["title"]), E(I.IDX[v].get("outcome", ""))) for v in vs)
        drs = sorted({d["id"]: d for f in F for d in I.reviews(f)}.values(), key=lambda d: d["review_date"])
        drow = "".join("<li data-row data-lcs='%s'>%s Stage %s · %s · %s</li>" % (I.REG[d["stage"]]["lifecycle_stage"], R(path, d["id"]), I.REG[d["stage"]]["code"], E(d["review_date"]), E(d.get("decision", ""))) for d in drs)
        ver = [s.cat("compliance", "Compliance", ("<div class=tw><table><thead><tr><th>Document</th><th>FDPS</th><th>Line items</th><th>Compliance Statements</th></tr></thead><tbody>%s</tbody></table></div>" % crow if crow else "<p class=empty>No FDPS here yet.</p>") + (("<h3>Non-compliant ranges</h3><ul class=rows>%s</ul>" % ncl) if ncs else ""), len(cs), "<span class='chip bad'>%d Non-compliant</span>" % len(ncs) if ncs else ""),
               s.cat("verifications", "Verifications", ("<ul class=rows>%s</ul>" % vrow) if vs else "<p class=empty>None yet.</p>", len(vs)),
               s.cat("reviews", "Reviews", ("<ul class=rows>%s</ul>" % drow) if drs else "<p class=empty>None yet.</p>", len(drs))]
        pg = I.pages.get(sub["id"])
        if pg and pg.get("hub") != "FW":
            ifs = "<p class=small>From %s. %s</p><ul class=rows>%s</ul>" % (R(path, pg["id"]), "Flows to every FDPS whose lead Sub-system is a Sub-structure with a Part Instance homed here (R-09)." if I.PAR[sub["id"]] in I.STR else "Flows to every FDPS with a Part Instance homed here.", "".join("<li data-row>%s</li>" % L(path, y) for y in pg["interfaces"])); nif = len(pg["interfaces"])
        else: ifs = fw_body; nif = 0
        tps = [I.team_page(f) for f in F]; dsc = sorted({d for t in tps for d in t.get("applicable_disciplines", [])})
        stk = [a for a in I.of("Role Assignment") if a["status"] == "Active" and a["area"]["ref"] in (sub["id"], sys_["id"])]
        drows = "".join("<li data-row data-disc='%s'>%s</li>" % (d, L(path, d, I.lab(d).split(" (")[0])) for d in dsc) + "".join("<li>%s · %s (%s)</li>" % (s.ul(path, a["person"]), E(a["role"]), L(path, a["area"]["ref"])) for a in stk)
        con = [s.cat("ifs", "Interfacing Systems", ifs, nif), s.cat("disc", "Disciplines and Stakeholders", ("<ul class=rows>%s</ul>" % drows) if drows else "<p class=empty>None recorded.</p>", len(dsc) + len(stk))]
        iss = sorted({i["id"]: i for i in I.of("Issue") if any(f["id"] in I.lk(i, "Affects") for f in F) or any(c.get("issue") == i["id"] for c in cs)}.values(), key=lambda i: i["id"])
        irow = "".join("<li data-row class='%s'%s data-lcs='%s'>%s %s <span class='chip %s'>%s</span> <small>level %d · owner %s</small></li>" % ("op" if i["status"] != "Closed" else "", (" data-eff='%s'" % rngs(i["effectivity"])) if isinstance(i.get("effectivity"), dict) else "", " ".join(i.get("lifecycle_stage", [])), R(path, i["id"]), E(i["title"]), "bad" if i["status"] != "Closed" else "ok", E(i["status"]), max(i["scores"].values()), s.ul(path, i["owner"])) for i in iss)
        lls = [l for l in I.of("Lesson Learned") if sub["id"] in l.get("sub_system", []) or sys_["id"] in l.get("system", [])] + [l for l in s.R if l["type"] == "Lesson Learned" and l.get("hub") == "FW" and sys_["id"] in l.get("system", [])]
        lrow = "".join("<li data-row data-lcs='%s' data-disc='%s' data-dty='%s'>%s %s</li>" % (" ".join(l.get("lifecycle_stage", [])), " ".join(l.get("discipline", [])), " ".join(l.get("design_type", []) or ["ALL"]), R(path, l["id"]) if l.get("hub") != "FW" else s.link(path, l["id"], l["id"]), E(l["title"])) for l in lls)
        wk = [s.cat("issues", "Issues", ("<ul class=rows>%s</ul>" % irow) if iss else "<p class=empty>No Issue affects the FDPSs here.</p>", len(iss)), s.cat("lessons", "Lessons Learned", ("<ul class=rows>%s</ul><p class=nf>Matched by tag: System or Sub-system (2G.3).</p>" % lrow) if lls else "<p class=empty>No lesson is tagged to this System or Sub-system.</p>", len(lls))]
        tiles = [dict(label="FDPS", n=len(F), cat="fdps"), dict(label="EDRs", n=len(ed), cat="edrs"), dict(label="TSMs", n=len(ts), cat="tsms"), dict(label="Non-compliant", n=len(ncs), cat="compliance", sel=".nc", bad=bool(ncs)),
                 dict(label="Open Issues", n=sum(1 for i in iss if i["status"] != "Closed"), cat="issues", sel=".op", bad=any(i["status"] != "Closed" for i in iss)), dict(label="Lessons", n=len(lls), cat="lessons")]
        img = "fuel-feed.svg" if sub["id"] == "VR-SUB-0032" else "model-placeholder.svg"
        return {"req": req, "ver": ver, "prod": [fd], "con": con, "wk": wk}, tiles, (["<span class='chip ok'>%d FDPS</span>" % len(F)] if F else []), img, "Model preview: image in place of the live model until real models exist (1.12, 5.16)", "{PROJ} production data for this node."
    # ------------------------------------------------------------------
    def build(s):
        super().build(); I = s.I; U = s.url; L = s.link; R = s.rl
        P = s.P; fds = sorted(I.of("FDPS"), key=lambda f: f["fdps_number"])
        effs = sorted(I.of("Effectivity"), key=lambda e: e["number"])
        ph = '<span class="badge co">{PROJ} (fictional)</span>'
        # ---- project home replaces the framework home
        cs = [c for c in I.of("Compliance Statement")]; openiss = [i for i in I.of("Issue") if i["status"] != "Closed"]; openact = [a for a in I.of("Action") if a["status"] != "Closed"]
        cards = [("FDPSs", "fdps/", len(fds)), ("Part Instances", "records/part-instances/", len(I.of("Part Instance"))), ("Requirements and TSMs", "records/requirements/", len(I.of("Requirement")) + len(I.of("TSM"))),
                 ("Compliance Statements", "reports/coverage/", len(cs)), ("Open Issues", "records/issues/", len(openiss)), ("Open Actions", "records/actions/", len(openact)), ("Design Reviews", "records/design-reviews/", len(I.of("Design Review"))), ("Effectivities", "records/effectivities/", len(effs)),
                 ("EDRs", "edrs/", len(I.edrs())), ("TSMs", "tsms/", len(I.of("TSM"))), ("People", "users/", len(I.of("User"))), ("Admin: users and access", "admin/users/", len(I.of("Project Assignment")))]
        body = '<div class="note"><b>Demo content.</b> {PROJ}, {PNAME}, is entirely fictional. Every person, part, requirement, analysis and issue is invented to exercise the Production Hub and is not real engineering data.</div>'
        body += "<p>Production Hub for %s, built on %s (Framework Version %s). Framework pages below carry {PROJ}'s tailoring; production data appears on tree pages, FDPS pages, record registers and reports.</p>" % (E(P["name"]), E(build_site.VERSION_LABEL), E(P["framework_version"]))
        body += '<div class="cards">' + "".join('<a class="card" href="%s"><div class="n">%d</div><div>%s</div></a>' % (u, n, E(t)) for t, u, n in cards) + "</div>"
        body += "<h2>FDPSs</h2>" + s.fdps_table("", fds)
        body += "<h2>Release status by effectivity</h2>" + s.eff_table("", fds, effs)
        body += '<h2>Where to go</h2><ul><li><a href="reports/coverage/">Requirement coverage</a>, <a href="reports/release-gate/">release gate status</a>, <a href="reports/open-flags/">open Review Flags</a></li><li><a href="records/">Record registers</a> and <a href="tailoring/">Tailoring Records</a></li><li><a href="feedback/">Framework gaps found while filling the Demo</a></li><li>Framework (generic, public): <a href="%s">Engineering Hub Framework</a></li></ul>' % FW_URL
        body += "<h2>Masters</h2><p>Part and FDPS revisions are released in the PLM system (release master); the Hub records frozen copies and baselines (6A.13). Effectivity maximum: %d. Sub-system pages use the v8 layout with an effectivity filter; ranges are shown on every record.</p>" % P.get("effectivity_max", 60)
        s.pages[""].update(title="{PROJ} Production Hub: {PNAME}", body=body, rid=P["id"], meta=s.metap(P["id"], owner=P["owner"], vs=P["verification_status"], reviewed=P["modified_at"][:10]))
        # ---- FDPS index and pages
        s.add("fdps/", "FDPSs", "<p>Every FDPS of {PROJ}. An FDPS is a released installation design package of Part Instances owned by one Design Sub-team (1.7). Part Instances have no pages of their own: they are listed in the FDPS population and the <a href='../records/part-instances/'>Part Instance register</a>.</p>" + s.fdps_table("fdps/", fds), "FDPS", "index", [("", "Home")], s.metap("register FDPS", owner="{PROJ}"))
        for f in fds: s.fdps_page(f, effs)
        s.doc_pages(fds); s.user_pages()
        # ---- production data on tree pages
        pis = I.of("Part Instance"); ais = I.of("Assembly Instance")
        def inst_rows(frm, items):
            if not items: return "<p>No Part Instance of {PROJ} here yet.</p>"
            h = "<table><thead><tr><th scope=col>Instance</th><th scope=col>Position</th><th scope=col>Part</th><th scope=col>FDPS</th><th scope=col>Located at</th><th scope=col>Homed in</th><th scope=col>Exists</th></tr></thead><tbody>"
            for p in sorted(items, key=lambda x: x["id"]):
                d = (I.lk(p, "Instance of") or [None])[0]; fd = I.fdps_of(p["id"]) or next((I.fdps_of(a["id"]) for a in ais if p["id"] in I.lk(a, "Contains")), None)
                h += "<tr><td id='%s'>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (E(p["id"]), E(p["id"]), E(p.get("position_name", p["title"])), R(frm, d, (I.IDX.get(d) or {}).get("part_number") or d), R(frm, fd, I.IDX[fd]["fdps_number"]) if fd else "", ", ".join(L(frm, x, x if False else None) for x in I.lk(p, "Located at")), ", ".join(L(frm, x) for x in I.lk(p, "Homed in")), rng(p["existence"]))
            return h + "</tbody></table>"
        for bs in s.by["BS"]:
            path = U[bs["id"]]; here = [p for p in pis + ais if bs["id"] in I.lk(p, "Located at")]
            if here: s.pages[path]["body"] += "<h2>Items located here %s</h2>%s" % (ph, inst_rows(path, here))
        for y in s.by["SYS"]:
            path = U[y["id"]]; fl = [f for f in fds if y["id"] in I.systems(f)]
            subs = [x["id"] for x in s.kids("SUB", y["id"])]
            ed = [d for d in I.edrs() if set(d["sub_system_tags"]) & set(subs)]; ts = sorted({t["id"]: t for x in subs for t, _ in I.tsms_for_sub(x)}.values(), key=lambda t: t["manual_code"])
            if fl or ed or ts: s.pages[path]["body"] += "<h2>{PROJ} FDPSs with Part Instances in this System %s</h2><ul>%s</ul><h2>Requirement documents (EDRs tagged to its Sub-systems)</h2><ul>%s</ul><h2>TSMs reaching its Sub-systems</h2><ul>%s</ul><p>Above FDPS level documents are listed, not line items; line items are on FDPS pages (5.21).</p>" % (ph, "".join("<li>%s</li>" % R(path, f["id"], "%s %s" % (f["fdps_number"], f["title"])) for f in fl) or "<li>None</li>", "".join("<li>%s (%d line items)</li>" % (R(path, d["id"], "%s %s" % (d["doc_code"], d["title"])), len(I.edr_items(d))) for d in ed) or "<li>None</li>", "".join("<li>%s</li>" % R(path, t["id"], "%s %s" % (t["manual_code"], t["title"])) for t in ts) or "<li>None</li>")
        for st in s.by["DST"]:
            path = U[st["id"]]; fl = [f for f in fds if f["owning_sub_team"] == st["id"]]
            pg = I.pages.get(st["id"])
            if fl or (pg and pg.get("hub") != "FW"):
                s.pages[path]["body"] += "<h2>FDPSs owned %s</h2>%s" % (ph, s.fdps_table(path, fl) if fl else "<p>None</p>")
                if pg and pg.get("hub") != "FW":
                    s.pages[path]["body"] += "<h2>{PROJ} stage sections</h2><p>Tailored on %s.</p>%s" % (R(path, pg["id"]), "".join("<h3>Stage %s</h3><p>Sign-off: %s</p><p>Checklist items: %s</p>" % (I.REG[x["stage"]]["code"], ", ".join(L(path, d, I.lab(d).split(" (")[0]) for d in x["sign_off_disciplines"]), ", ".join(E(c["item_id"]) for c in x["checklist_items"])) for x in pg["stage_sections"]))
        for t in s.by["DT"]:
            pg = I.pages.get(t["id"])
            if pg and pg.get("hub") != "FW":
                path = U[t["id"]]
                s.pages[path]["body"] += "<h2>{PROJ} lists %s</h2><p>Design Types: %s</p><p>Disciplines: %s</p><p>Tailored on %s.</p>" % (ph, ", ".join(L(path, x) for x in pg["applicable_design_types"]), ", ".join(L(path, x) for x in pg["applicable_disciplines"]), R(path, pg["id"]))
        na = I.na_disciplines()
        for d in na:
            tr = next(t for t in I.of("Tailoring Record") if isinstance(t.get("payload"), dict) and t["payload"].get("discipline") == d)
            s.pages[U[d]]["body"] = "<div class='note'><b>Not applicable to {PROJ}</b> (%s, approved by %s). Its checklist items are removed from {PROJ} review templates.</div>" % (R(U[d], tr["id"]), E(tr.get("approved_by", ""))) + s.pages[U[d]]["body"]
        # ---- registers of records
        s.add("records/", "Record registers", "<p>Every {PROJ} record type. Each register row opens a record detail panel inside the register; there are no pages for individual Part Instances or records (plan 3.2).</p><ul>%s</ul>" % "".join("<li><a href='%s/'>%s</a> (%d)</li>" % (u, E(t), len(I.of(t))) for t, u in TYPES if I.of(t)), "RECORDS", "index", [("", "Home")], s.metap("RECORDS", owner="{PROJ}"))
        for t, u in TYPES:
            rs = sorted(I.of(t), key=lambda r: r["id"])
            if not rs: continue
            s.add("records/%s/" % u, t + " register", s.register_html("records/%s/" % u, t, rs), "register " + t, "register", [("", "Home"), ("records/", "Records")], s.metap("register " + t, owner="{PROJ}"), text=" ".join(r["id"] + " " + r["title"] for r in rs))
        # ---- tailoring
        trs = I.of("Tailoring Record")
        s.add("tailoring/", "Tailoring Records", "<p>{PROJ}'s changes to the framework it adopted (6.4, 6.11). Annex A placeholder lists and interface lists are replaced; Low Observability is not applicable.</p>" + s.register_html("tailoring/", "Tailoring Record", trs), "TAILORING", "register", [("", "Home")], s.metap("TAILORING", owner="{PROJ}"))
        # ---- reports
        s.add("reports/coverage/", "Requirement coverage", s.coverage(fds), "REPORT-COVERAGE", "report", [("", "Home")], s.metap("REPORT-COVERAGE", owner="Hub (derived)", vs="Derived from verified records"))
        s.add("reports/release-gate/", "Release gate status", s.gate_report(fds, effs), "REPORT-GATE", "report", [("", "Home")], s.metap("REPORT-GATE", owner="Hub (derived)", vs="Derived from verified records"))
        fl = I.of("Review Flag")
        s.add("reports/open-flags/", "Review Flags", "<p>Flags raised by changes along links (2I.2) and by cross-FDPS Secures links (R-18: no confirmation; the other owner records Accept or Query).</p>" + s.register_html("reports/open-flags/", "Review Flag", fl), "REPORT-FLAGS", "report", [("", "Home")], s.metap("REPORT-FLAGS", owner="Hub (derived)"))
        s.add("feedback/", "Framework gaps found while filling the Demo", s.feedback(), "FEEDBACK", "reference", [("", "Home")], s.metap("FEEDBACK", owner="{PROJ}"))
    # ------------------------------------------------------------------
    def fdps_table(s, frm, fds):
        I = s.I; h = "<table><thead><tr><th scope=col>FDPS</th><th scope=col>Title</th><th scope=col>Owning Sub-team</th><th scope=col>Lead Sub-system</th><th scope=col>Status</th><th scope=col>Revisions</th></tr></thead><tbody>"
        for f in fds:
            h += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (s.rl(frm, f["id"], f["fdps_number"]), E(f["title"]), s.link(frm, f["owning_sub_team"]), s.link(frm, f["lead_sub_system"]), E(f["status"]), ", ".join("%s (%s, %s)" % (r["revision"], rng(r["effectivity"]), r["status"]) for r in I.revisions(f)) or "none")
        return h + "</tbody></table>"
    def nc_ranges(s, f): return [c for c in s.I.statements(f) if c["position"] == "Non-compliant"]
    def eff_table(s, frm, fds, effs):
        I = s.I; h = "<table><thead><tr><th scope=col>FDPS</th>" + "".join("<th scope=col>Eff. %d (%s)</th>" % (e["number"], E(e.get("serial", ""))) for e in effs) + "</tr></thead><tbody>"
        for f in fds:
            h += "<tr><td>%s</td>" % s.rl(frm, f["id"], f["fdps_number"])
            for e in effs:
                n = e["number"]; r = I.effective_revision(f, n); nc = [c for c in s.nc_ranges(f) if c["effectivity"]["from"] <= n <= c["effectivity"]["to"]]
                cell = ("rev %s" % r["revision"]) if r else "no released revision"
                if nc: cell += " · <b>Non-compliant</b>, release blocked (%s)" % ", ".join(s.rl(frm, c["id"]) for c in nc)
                h += "<td>%s</td>" % cell
            h += "</tr>"
        return h + "</tbody></table>"
    def fdps_page(s, f, effs):
        I = s.I; path = s.url[f["id"]]; R = s.rl; L = s.link; F = f["id"]
        mems = I.members(f); revs = I.revisions(f); cs = I.statements(f); inh = I.inherited(f); ifs = I.interfaces(f); brk = {b["system"]: b for b in f.get("interface_breaks", [])}
        ap = f.get("lead_sub_system_approval", {})
        nc = s.nc_ranges(f)
        b = ""
        if nc: b += "<div class='note'><b>Release blocked for effectivities %s.</b> %s is Non-compliant and its Issue %s is %s. No FDPS revision can be released for these effectivities until it is resolved (6A.17, decision 9).</div>" % (", ".join(rng(c["effectivity"]) for c in nc), ", ".join(R(path, c["id"]) for c in nc), ", ".join(R(path, c.get("issue")) for c in nc), ", ".join(E(I.IDX[c["issue"]]["status"]) for c in nc if c.get("issue") in I.IDX))
        b += "<div class='meta'><span class=k>FDPS number</span><span>%s</span><span class=k>Owning Sub-team</span><span>%s</span><span class=k>Lead Sub-system</span><span>%s · set by %s %s, approved by %s %s (R-15)</span><span class=k>Lifecycle stage</span><span>%s</span><span class=k>Status</span><span>%s</span><span class=k>Effective revisions</span><span>%s</span></div>" % (
            E(f["fdps_number"]), L(path, f["owning_sub_team"]), L(path, f["lead_sub_system"]), E(ap.get("set_by", "")), E(ap.get("set_at", "")[:10]), E(ap.get("approved_by", "")), E(ap.get("approved_at", "")[:10]), L(path, f["lifecycle_stage"]), E(f["status"]), "; ".join("rev %s for %s (%s)" % (r["revision"], rng(r["effectivity"]), r["status"]) for r in revs) or "none yet")
        b += "<p><b>Owner:</b> %s · <b>Contributors:</b> %s</p>" % (s.ul(path, f["owner"]), ", ".join(s.ul(path, c) for c in f.get("contributors", [])) or "none")
        b += s.line_items_html(path, f)
        # population by Part Definition
        b += "<h2>Population (current, grouped by Part or Assembly Definition)</h2><table><thead><tr><th scope=col>Definition</th><th scope=col>Instance</th><th scope=col>Position</th><th scope=col>Homed in</th><th scope=col>Located at</th><th scope=col>Exists</th><th scope=col>Links</th></tr></thead><tbody>"
        rows = []
        for m in mems:
            r = I.IDX[m]; d = (I.lk(r, "Instance of") or [""])[0]; rows.append((d, r))
            for sub in I.lk(r, "Contains"): rows.append(((I.lk(I.IDX[sub], "Instance of") or [""])[0], dict(I.IDX[sub], _in=m)))
        for d, r in sorted(rows, key=lambda x: (x[0], x[1]["id"])):
            ex = ", ".join("%s %s" % (k, R(path, t) if not t.startswith("VR-") else L(path, t)) for k in ("Secures", "Supports") for t in I.lk(r, k))
            b += "<tr><td>%s</td><td>%s%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (R(path, d, (I.IDX.get(d) or {}).get("part_number") or d), E(r["id"]), (" (in %s)" % E(r["_in"])) if r.get("_in") else "", E(r.get("position_name", r["title"])), ", ".join(L(path, x) for x in I.lk(r, "Homed in")) or "(assembly)", ", ".join(L(path, x) for x in I.lk(r, "Located at")), rng(r["existence"]), ex)
        b += "</tbody></table><p>Part Instances have no pages; full rows are in the %s.</p>" % ("<a href='%s'>Part Instance register</a>" % s.rel(path, "records/part-instances/"))
        b += "<h2>Derived Systems and Major Units</h2><p>Systems: %s. Major Units: %s. Build Stations: %s.</p>" % (", ".join(L(path, y) for y in I.systems(f)), ", ".join(L(path, m) for m in I.major_units(f)), ", ".join(L(path, x) for x in I.stations(f)))
        # interfaces
        rt = {"a": "(a) Sub-system page list", "b": "(b) Sub-structure page list", "c": "(c) Supports link"}
        b += "<h2>Interfacing Systems (%d inherited, %d broken)</h2><p>%s</p><table><thead><tr><th scope=col>System</th><th scope=col>Routes</th><th scope=col>State</th></tr></thead><tbody>" % (len(ifs), len(brk), "Structural FDPS: the lists of every Sub-structure it touches flow to it (R-09)." if I.is_structural(f) else "Non-structural FDPS: lists of its non-structural Sub-system pages and Supports links; Sub-structure lists do not flow to it.")
        for y in sorted(ifs):
            st = ("<b>Broken</b>: %s (by %s, approved by %s %s)" % (E(brk[y]["reason"]), E(brk[y]["by"]), E(brk[y]["approved_by"]), E(brk[y]["approved_at"][:10]))) if y in brk else "Interfacing"
            b += "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (L(path, y), "; ".join("%s %s" % (rt[x[0]], s.rl(path, x[2:]) if not x[2:].startswith("VR-") else L(path, x[2:])) for x in ifs[y]), st)
        b += "</tbody></table>"
        fi = I.fdps_interfaces(f)
        if fi:
            b += "<h2>FDPS interfaces (cross-FDPS Secures, R-18)</h2><table><thead><tr><th scope=col>Other FDPS</th><th scope=col>Fastener</th><th scope=col>Part held</th><th scope=col>Review Flag decision</th></tr></thead><tbody>"
            for x in fi:
                tgt = F if x["direction"] == "in" else x["fdps"]
                fl = [r for r in I.of("Review Flag") if r.get("fdps_interface") and r["flagged_object"] == tgt and r["triggering_object"] == x["fastener"]]
                b += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (R(path, x["fdps"], I.IDX[x["fdps"]]["fdps_number"]), E(x["fastener"]), E(x["held"]), "; ".join("%s %s by %s" % (R(path, r["id"]), E(r["decision"]), E(r.get("decided_by", ""))) for r in fl) or "flag pending")
            b += "</tbody></table><p>No confirmation is required; the owner of the other FDPS records Accept or Query on the flag.</p>"
        # requirements and TSMs
        def basis(x):
            k = x["basis"]
            if k == "Direct": return "Direct (Satisfied by %s)" % E(x["item"])
            return "%s %s" % (E(k), s.link(path, x.get("node") or x.get("design_type") or x.get("system") or x.get("discipline")))
        for kind, pre in (("Requirements", "REQ"), ("TSMs", "TSM")):
            ks = sorted(k for k in inh if k.startswith(pre))
            b += "<h2>%s (%d)%s</h2><table><thead><tr><th scope=col>%s</th><th scope=col>Bases (inherited and direct shown separately)</th><th scope=col>Compliance by effectivity</th></tr></thead><tbody>" % (kind, len(ks), " · a TSM reaches the FDPS when any tag matches (OR)" if pre == "TSM" else "", kind[:-1])
            for k in ks:
                r = I.IDX[k]; rows_ = sorted([c for c in cs if c["requirement"] == k], key=lambda c: c["effectivity"]["from"])
                b += "<tr><td>%s<br><small>%s</small></td><td>%s</td><td>%s</td></tr>" % (R(path, k, "%s %s" % (r.get("req_number") or r.get("manual_code"), r["title"])), E(r.get("statement", "")), "<br>".join(basis(x) for x in inh[k]),
                    "<br>".join("%s: <b>%s</b> %s%s%s" % (rng(c["effectivity"]), E(c["position"]), R(path, c["id"]), (" · evidence " + ", ".join(R(path, v) for v in c["evidence"])) if c["evidence"] else "", (" · " + E(c.get("reason", ""))) if c["position"] != "Compliant" else "") for c in rows_))
            b += "</tbody></table>"
        # reviews
        drs = I.reviews(f)
        b += "<h2>Design reviews</h2>"
        if not drs: b += "<p>None yet.</p>"
        for d in drs:
            snap = next((x for x in I.of("Review Snapshot") if x["design_review"] == d["id"]), None)
            acts = [a for a in I.of("Action") if d["id"] in I.lk(a, "Raised at")]; cks = [c for c in I.of("Checklist Response") if c["stage"] == d["stage"] and c["fdps_revision"] in I.lk(d, "Covers")]
            rsk = [x for x in I.of("Risk") if x.get("source", {}).get("ref") == d["id"]]
            b += "<h3>%s · Stage %s · %s · %s</h3>" % (R(path, d["id"]), I.REG[d["stage"]]["code"], E(d["review_date"]), E(d.get("decision", "")))
            b += "<p>%s Chair %s. Covers %s. Snapshot %s (baseline %s).%s</p>" % (E(d["title"]), E(d["chair"]), ", ".join(R(path, x) for x in I.lk(d, "Covers")), R(path, snap["id"]) if snap else "none", R(path, snap.get("baseline")) if snap else "", " Re-review of %s." % R(path, d["re_review"]["follows_review"]) if d.get("re_review") else "")
            b += "<table><thead><tr><th scope=col>Sign-off Discipline</th><th scope=col>Position</th><th scope=col>By</th></tr></thead><tbody>%s</tbody></table>" % "".join("<tr><td>%s</td><td>%s%s</td><td>%s</td></tr>" % (s.link(path, a["discipline"], I.lab(a["discipline"]).split(" (")[0]), E(a["position"]), ((" · conditions " + ", ".join(R(path, c) for c in a.get("conditions", []))) if a.get("conditions") else "") + ((" (carried forward from %s)" % R(path, a["carried_forward_from"])) if a.get("carried_forward_from") else ""), E(a["by"])) for a in d["discipline_agreements"])
            b += "<table><thead><tr><th scope=col>Interfacing System</th><th scope=col>Position</th><th scope=col>Reason</th><th scope=col>By</th></tr></thead><tbody>%s</tbody></table>" % "".join("<tr><td>%s</td><td>%s%s</td><td>%s</td><td>%s</td></tr>" % (s.link(path, a["system"]), E(a["position"]), (" (carried forward)" if a.get("carried_forward_from") else ""), E(a.get("reasons", "")), E(a["by"])) for a in d["interface_agreements"])
            b += "<p>Checklist responses: %s. Actions: %s. Risks: %s.</p>" % (", ".join("%s %s" % (E(c["item_id"]), E(c["response"])) for c in cks) or "none", ", ".join("%s (%s)" % (R(path, a["id"]), E(a["status"])) for a in acts) or "none", ", ".join(R(path, x["id"]) for x in rsk) or "none")
        # revisions, baselines, gate
        b += "<h2>Revisions, baselines and release gate</h2>"
        for r in revs:
            ga = r.get("gate_attempts", [])
            b += "<h3>Rev %s · effectivity %s · %s</h3><p>Released %s by %s. Passed reviews: %s%s. Baselines: %s.</p>" % (E(r["revision"]), rng(r["effectivity"]), E(r["status"]), E(r.get("released_at", "")[:10]), E(r.get("released_by", "")), ", ".join(R(path, x) for x in r.get("passed_reviews", [])) or "none", (" · C pass carried forward from %s" % R(path, r["carried_forward_review"]["review"])) if r.get("carried_forward_review") else "", ", ".join(R(path, x) for x in r.get("baselines", [])))
            if ga: b += "<p>Gate attempts: %s.</p>" % "; ".join("%s %s (open: %s)" % (E(x["at"][:10]), E(x["result"]), ", ".join(R(path, a) for a in x.get("open_actions", []))) for x in ga)
            g = r.get("gate_confirmation") or {}
            b += "<p>Gate confirmation: %s %s · open Actions %d · Non-compliant statements %d. Release assessment by %s: %s</p>" % (E(g.get("confirmed_by", "")), E(g.get("at", "")[:10]), len(g.get("open_actions", [])), len(g.get("non_compliant_statements", [])), E(r.get("release_assessment", {}).get("assessed_by", "")), E(r.get("release_assessment", {}).get("rationale", "")))
        b += "<h3>Configuration by effectivity</h3>" + s.eff_table(path, [f], effs)
        crs = [c for c in I.of("Change Record") if any(x["fdps"] == F for x in c.get("fdps_assessments", []))]
        b += "<h2>Change Records</h2><ul>%s</ul>" % ("".join("<li>%s %s: %s</li>" % (R(path, c["id"]), E(c["title"]), "; ".join(("substantial (%s)" % ", ".join(x["criteria"])) if x["substantial"] else "not substantial" for x in c["fdps_assessments"] if x["fdps"] == F)) for c in crs) or "<li>None</li>")
        iss = [i for i in I.of("Issue") if any(c.get("issue") == i["id"] for c in cs) or F in I.lk(i, "Affects")]
        b += "<h2>Issues</h2><ul>%s</ul>" % ("".join("<li>%s %s (%s, level %d)</li>" % (R(path, i["id"]), E(i["title"]), E(i["status"]), max(i["scores"].values())) for i in iss) or "<li>None</li>")
        s.add(path, "FDPS %s: %s" % (f["fdps_number"], f["title"]), b, F, "fdps", [("", "Home"), ("fdps/", "FDPSs")], s.metap(F, owner=f["owner"], vs=f["verification_status"], reviewed=f["modified_at"][:10]), trees=[("Design", "Full Aircraft > %s > %s > %s" % (I.lab(I.PAR[f["owning_sub_team"]]), I.lab(f["owning_sub_team"]), f["fdps_number"]))], preview=True)
    def line_items_html(s, path, f):
        I = s.I; li = I.line_items(f); m = I.maturity(f); R = s.rl
        h = "<h2>Line items (%d): EDR requirements and TSM statements</h2><p>Maturity: <b>%d of %d reviewed</b> (Kept %d, Broken %d, Superseded (auto) %d; unreviewed %d; TSM supersessions awaiting Design Authority bulk confirmation %d). Every inherited line item applies until it is Kept or Broken; once a level has defined links, flowed-down items they do not reach are Superseded (auto) (6B.7, 6B.7A). Stage C entry and the release gate need no unreviewed line item (6C.11, 6C.15).</p>" % (m["total"], m["reviewed"], m["total"], m["kept"], m["broken"], m["superseded"], m["unreviewed"], m["pending_bulk"])
        for d in sorted({x["doc"] for x in li}, key=lambda d: (not d.startswith("EDR"), d)):
            xs = [x for x in li if x["doc"] == d]; doc = I.IDX[d]
            h += "<h3>%s</h3><table><thead><tr><th scope=col>Line item</th><th scope=col>Route</th><th scope=col>State</th><th scope=col>Review</th></tr></thead><tbody>" % R(path, d, "%s %s (issue %s)" % (doc.get("doc_code") or doc.get("manual_code"), doc["title"], doc.get("issue")))
            for x in xs:
                rv = x["review"] or {}
                nm = ("%s %s" % (I.IDX[x["item"]]["req_number"], I.IDX[x["item"]]["title"])) if x["kind"] == "EDR" else "Statement %s" % x["clause"]
                stx = I.IDX[x["item"]].get("statement") if x["kind"] == "EDR" else next((c["statement"] for c in I.IDX[x["item"]]["statements"] if c["clause"] == x["clause"]), "")
                det = ""
                if rv.get("state") == "Broken": det = "%s · approved by %s %s" % (E(rv.get("reason", "")), s.ul(path, rv.get("approved_by")), E(rv.get("approved_at", "")[:10]))
                elif rv.get("state") == "Superseded (auto)": det = "by %s%s" % (", ".join(R(path, y) if y in I.IDX else E(y) for y in rv.get("superseded_by", [])), (" · bulk confirmed %s" % R(path, rv["bulk_confirmation"])) if rv.get("bulk_confirmation") else (" · awaiting Design Authority bulk confirmation" if x["kind"] == "TSM" else ""))
                elif rv.get("state") == "Kept": det = "by %s" % s.ul(path, rv.get("author"))
                h += "<tr><td>%s<br><small>%s</small></td><td>%s</td><td><span class='chip %s'>%s</span></td><td>%s%s</td></tr>" % (R(path, x["item"], nm) if x["kind"] == "EDR" else E(nm), E(stx), E("; ".join(x["route"])), STC.get(x["state"], ""), E(x["state"]), det, (" · " + R(path, rv["id"])) if rv else "")
            h += "</tbody></table>"
        return h
    def doc_pages(s, fds):
        I = s.I; L = s.link; R = s.rl
        ed = I.edrs()
        s.add("edrs/", "EDRs: Engineering Design Requirements", "<p>Requirement Documents of kind EDR. Each groups Requirement line items and is tagged at document level to Sub-systems; an FDPS inherits every EDR tagged to a Sub-system in which one of its Part Instances is homed (6B.1A, 6B.2).</p><table><thead><tr><th scope=col>EDR</th><th scope=col>Title</th><th scope=col>Issue</th><th scope=col>Line items</th><th scope=col>Sub-system tags</th></tr></thead><tbody>%s</tbody></table>" % "".join("<tr><td>%s</td><td>%s</td><td>%d</td><td>%d</td><td>%s</td></tr>" % (R("edrs/", d["id"], d["doc_code"]), E(d["title"]), d["issue"], len(I.edr_items(d)), ", ".join(L("edrs/", t) for t in d["sub_system_tags"])) for d in ed), "EDR-INDEX", "index", [("", "Home")], s.metap("register Requirement Document", owner="{PROJ}"))
        for d in ed:
            p = s.url[d["id"]]; its = I.edr_items(d)
            inh = [(f, [x for x in I.line_items(f) if x["doc"] == d["id"]]) for f in fds]; inh = [(f, xs) for f, xs in inh if xs]
            b = "<div class='meta'><span class=k>Code</span><span>%s</span><span class=k>Kind</span><span>EDR</span><span class=k>Issue</span><span>%d (%s)</span><span class=k>Owner</span><span>%s</span><span class=k>Sub-system tags</span><span>%s</span></div>" % (E(d["doc_code"]), d["issue"], E(d["status"]), s.ul(p, d["owner"]), ", ".join(L(p, t) for t in d["sub_system_tags"]))
            b += "<h2>Line items (%d)</h2><table><thead><tr><th scope=col>Number</th><th scope=col>Title and statement</th><th scope=col>Level</th><th scope=col>Revision</th><th scope=col>Optional narrowing (Allocated to)</th></tr></thead><tbody>%s</tbody></table>" % (len(its), "".join("<tr id='%s'><td>%s</td><td>%s<br><small>%s</small></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (E(q["id"]), R(p, q["id"], q["req_number"]), E(q["title"]), E(q.get("statement", "")), L(p, q["level"]), q.get("line_item_revision", 1), ", ".join(L(p, x) for x in I.lk(q, "Allocated to")) or "none") for q in its))
            b += "<h2>FDPSs inheriting this EDR (%d)</h2><table><thead><tr><th scope=col>FDPS</th><th scope=col>Line-item states</th><th scope=col>Compliance</th></tr></thead><tbody>%s</tbody></table>" % (len(inh), "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (R(p, f["id"], f["fdps_number"]), ", ".join("%d %s" % (sum(1 for x in xs if x["state"] == k), E(k)) for k in sorted({x["state"] for x in xs})), ", ".join("%s %s" % (E(c["position"]), rng(c["effectivity"])) for c in I.statements(f) if I.IDX[c["requirement"]]["type"] == "Requirement" and I.edr_of(c["requirement"]) == d["id"]) or "none") for f, xs in inh))
            s.add(p, "EDR %s: %s" % (d["doc_code"], d["title"]), b, d["id"], "edr", [("", "Home"), ("edrs/", "EDRs")], s.metap(d["id"], owner=d["owner"], vs=d["verification_status"], reviewed=d["modified_at"][:10]))
        ts = sorted(I.of("TSM"), key=lambda t: t["manual_code"])
        s.add("tsms/", "TSMs: Technical Standards Manuals", "<p>Each TSM is tagged with Design Types, Disciplines and Systems, never with Sub-systems. It reaches an FDPS through a Part Design Type match, a System or Discipline tag, or the route Sub-system &gt; Design Type &gt; TSM (6B.5).</p><table><thead><tr><th scope=col>TSM</th><th scope=col>Title</th><th scope=col>Issue</th><th scope=col>Statements</th><th scope=col>Tags</th></tr></thead><tbody>%s</tbody></table>" % "".join("<tr><td>%s</td><td>%s</td><td>%d</td><td>%d</td><td>%s</td></tr>" % (R("tsms/", t["id"], t["manual_code"]), E(t["title"]), t["issue"], len(t["statements"]), ", ".join(L("tsms/", g, I.lab(g).split(" (")[0]) for g in I.lk(t, "Governs"))) for t in ts), "TSM-INDEX", "index", [("", "Home")], s.metap("register TSM", owner="{PROJ}"))
        for t in ts:
            p = s.url[t["id"]]; subs = [x for x in s.by["SUB"] if any(tt["id"] == t["id"] for tt, _ in I.tsms_for_sub(x["id"]))]
            inh = [(f, [x for x in I.line_items(f) if x["doc"] == t["id"]]) for f in fds]; inh = [(f, xs) for f, xs in inh if xs]
            b = "<div class='meta'><span class=k>Code</span><span>%s</span><span class=k>Issue</span><span>%d (%s)</span><span class=k>Owner</span><span>%s</span><span class=k>Tags (Governs)</span><span>%s</span><span class=k>Reached from Sub-systems</span><span>%s</span></div>" % (E(t["manual_code"]), t["issue"], E(t["status"]), s.ul(p, t["owner"]), ", ".join(L(p, g, I.lab(g).split(" (")[0]) for g in I.lk(t, "Governs")), ", ".join(L(p, x["id"]) for x in subs) or "none")
            b += "<h2>Statements (%d)</h2><table><thead><tr><th scope=col>Clause</th><th scope=col>Statement</th><th scope=col>Revision</th></tr></thead><tbody>%s</tbody></table>" % (len(t["statements"]), "".join("<tr><td>%s</td><td>%s</td><td>%d</td></tr>" % (E(c["clause"]), E(c["statement"]), c.get("revision", 1)) for c in t["statements"]))
            b += "<h2>FDPSs inheriting this TSM (%d)</h2><table><thead><tr><th scope=col>FDPS</th><th scope=col>Statement states</th></tr></thead><tbody>%s</tbody></table>" % (len(inh), "".join("<tr><td>%s</td><td>%s</td></tr>" % (R(p, f["id"], f["fdps_number"]), "; ".join("%s %s" % (E(x["clause"]), E(x["state"])) for x in xs)) for f, xs in inh))
            s.add(p, "TSM %s: %s" % (t["manual_code"], t["title"]), b, t["id"], "tsm", [("", "Home"), ("tsms/", "TSMs")], s.metap(t["id"], owner=t["owner"], vs=t["verification_status"], reviewed=t["modified_at"][:10]))
    def user_pages(s):
        I = s.I; U = sorted(I.of("User"), key=lambda u: u["display_name"]); pa = {a["user"]: a for a in I.of("Project Assignment")}
        er = {e["project_assignment"]: e for e in I.of("Effectivity Restriction")}; po = I.of("Permission Override"); ra = I.of("Role Assignment")
        effn = {e["id"]: e["number"] for e in I.of("Effectivity")}
        def acc(u):
            a = pa.get(u["id"])
            if not a: return "No active assignment", ""
            e = er.get(a["id"]); return a["access_role"], ("Restricted: aircraft " + ", ".join(str(effn[x]) for x in e["effectivity"])) if e else "All"
        rows = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (s.ul("users/", u["handle"]), E(u.get("role_note", "")), E(acc(u)[0]), E(acc(u)[1]), E(u["user_status"])) for u in U)
        s.add("users/", "People", "<p>Every person who uses the {PROJ} Production Hub is a User (5A.1). Owners and Contributors of every record link here. All people are fictional.</p><table><thead><tr><th scope=col>User</th><th scope=col>Role note</th><th scope=col>Access role</th><th scope=col>Effectivity</th><th scope=col>Status</th></tr></thead><tbody>%s</tbody></table>" % rows, "USERS", "index", [("", "Home")], s.metap("register User", owner="{PROJ}"))
        for u in U:
            p = s.url[u["handle"]]; a = pa.get(u["id"]); its = I.user_items(u["handle"])
            b = "<div class='note'>User page placeholder: more content is to be defined (5A.9).</div><div class='meta'><span class=k>Name</span><span>%s</span><span class=k>Role note</span><span>%s</span><span class=k>Status</span><span>%s</span><span class=k>Access on {PROJ}</span><span>%s · effectivity %s</span><span class=k>Permission overrides</span><span>%s</span><span class=k>Authority roles (Role register)</span><span>%s</span></div>" % (
                E(u["display_name"]), E(u.get("role_note", "")), E(u["user_status"]), E(acc(u)[0]), E(acc(u)[1]) or "n/a", "; ".join("%s %s on %s (%s)" % (E(o["effect"]), E(o["permission"]["action"]), E(o["permission"]["data_type"]), E(o["reason"])) for o in po if o["user"] == u["id"]) or "none",
                "; ".join("%s, %s" % (E(r["role"]), s.link(p, r["area"]["ref"]) if r["area"]["ref"] in s.url else E(r["area"]["ref"])) for r in ra if r["person"] == u["handle"]) or "none")
            by = {}
            for r in its: by.setdefault(r["type"], []).append(r)
            b += "<h2>Assigned items (%d)</h2>" % len(its) + ("".join("<h3>%s (%d)</h3><ul>%s</ul>" % (E(t), len(rs), "".join("<li>%s %s <span class='badge %s'>%s</span></li>" % (s.rl(p, r["id"]), E(r["title"]), "so" if r.get("owner") == u["handle"] else "co", "Owner" if r.get("owner") == u["handle"] else "Contributor") for r in rs[:60]) + ("<li>… %d more</li>" % (len(rs) - 60) if len(rs) > 60 else "")) for t, rs in sorted(by.items())) or "<p>None.</p>")
            s.add(p, "User: " + u["display_name"], b, u["id"], "user", [("", "Home"), ("users/", "People")], s.metap(u["id"], owner="Demo Admin", vs=u["verification_status"], reviewed=u["modified_at"][:10]))
        s.add("admin/users/", "Admin: users and access", s.admin_html(U, pa, er, po, ra, effn, acc), "ADMIN-USERS", "admin", [("", "Home")], s.metap("ADMIN-USERS", owner="Demo Admin"))
    def admin_html(s, U, pa, er, po, ra, effn, acc):
        I = s.I; effs = sorted(I.of("Effectivity"), key=lambda e: e["number"])
        data = [{"i": u["id"], "n": u["display_name"], "h": u["handle"], "note": u.get("role_note", ""), "st": u["user_status"], "u": s.rel("admin/users/", s.url[u["handle"]]),
                 "role": pa[u["id"]]["access_role"] if u["id"] in pa else "", "since": pa[u["id"]]["from_date"] if u["id"] in pa else "", "eff": [effn[x] for x in er[pa[u["id"]]["id"]]["effectivity"]] if u["id"] in pa and pa[u["id"]]["id"] in er else None,
                 "ov": ["%s %s on %s (%s%s)" % (o["effect"], o["permission"]["action"], o["permission"]["data_type"], o["reason"], (", expires " + o["expires_on"]) if o.get("expires_on") else "") for o in po if o["user"] == u["id"]],
                 "ra": ["%s, %s" % (r["role"], I.lab(r["area"]["ref"])) for r in ra if r["person"] == u["handle"]]} for u in U]
        n = lambda f: sum(1 for d in data if f(d))
        h = "<div class='note'><b>Demo UI only.</b> This is a static site: the edit panel below shows how an Admin sets access, but nothing you change is saved or sent anywhere. In a Production Hub this page is visible only to Admins on the project and framework administrators (5A.8). All people are fictional.</div>"
        h += "<style>.adm{display:grid;grid-template-columns:1fr 380px;gap:16px;align-items:start}.adm table tr{cursor:pointer}.adm tr.sel td{background:#EAF7F6}.pnl{border:1px solid #C9DCE0;border-top:4px solid #46C1BE;border-radius:10px;padding:12px 14px;position:sticky;top:10px;background:#fff}.pnl h3{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:#3E5663;margin:14px 0 4px}.pnl select{font:inherit}.pnl label{display:inline-flex;gap:4px;margin-right:10px;font-size:.9rem}.pnl ul{margin:4px 0;padding-left:18px;font-size:.9rem}.tb{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}.tb input{flex:1;min-width:200px;padding:6px 8px;border:1px solid #C9DCE0;border-radius:6px}#saved{color:#8A3B12;font-weight:600}@media(max-width:900px){.adm{grid-template-columns:1fr}}</style>"
        h += '<div class="cards">' + "".join('<div class="card"><div class="n">%d</div><div>%s</div></div>' % (v, E(k)) for k, v in [("Users", len(data)), ("Admins", n(lambda d: d["role"] == "Admin")), ("Design Lead or Design Authority", n(lambda d: d["role"] in ("Design Lead", "Design Authority"))), ("Restricted effectivity", n(lambda d: d["eff"])), ("Permission overrides", len(po)), ("Suspended", n(lambda d: d["st"] == "Suspended"))]) + "</div>"
        h += "<div class=tb><label for=uf class=skip>Search users</label><input id=uf type=search placeholder='Search users…'><button type=button class=btn id=addu>+ Add user (demo)</button></div><div class=adm><div><table id=ut><thead><tr><th scope=col>User</th><th scope=col>Access role (Project D)</th><th scope=col>Effectivity</th><th scope=col>Overrides</th><th scope=col>Status</th></tr></thead><tbody>"
        for k, d in enumerate(data):
            h += "<tr data-k='%d'><td><a href='%s'>%s</a><br><small>%s</small></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (k, d["u"], E(d["n"]), E(d["note"]), E(d["role"] or "none"), "Restricted: aircraft " + ", ".join(map(str, d["eff"])) if d["eff"] else "All", len(d["ov"]) or "–", E(d["st"]))
        h += "</tbody></table></div><aside class=pnl aria-label='Edit user (demo)'><h2 id=pn style='margin:0'>Select a user</h2><div id=pnote style='font-size:.85rem;color:#3E5663'></div><h3>Project assignment: Project D</h3><p><label>Access role <select id=prole>%s</select></label> <small id=psince></small></p><p>Effectivity <label><input type=radio name=pe value=all id=peall> All</label><label><input type=radio name=pe value=r id=per> Restricted</label></p><p id=peffs>%s</p><h3>Permission overrides</h3><ul id=pov></ul><h3>Authority roles (Role register)</h3><ul id=pra></ul><p><button type=button class=btn id=psave>Save</button> <button type=button class=btn id=psus>Suspend user</button> <span id=saved role=status></span></p></aside></div>" % (
            "".join("<option>%s</option>" % r for r in ("Admin", "Design Lead", "Design Authority", "Engineer", "Viewer")), "".join("<label><input type=checkbox value=%d> Aircraft %d</label>" % (e["number"], e["number"]) for e in effs))
        h += "<script>window.ADMIN_USERS=%s;(function(){var D=window.ADMIN_USERS,$=function(i){return document.getElementById(i)};function li(a){return a.length?a.map(function(x){return '<li>'+x.replace(/</g,'&lt;')+'</li>'}).join(''):'<li>None</li>'}function show(k){var d=D[k];document.querySelectorAll('#ut tr.sel').forEach(function(r){r.classList.remove('sel')});var tr=document.querySelectorAll('#ut tbody tr')[k];if(tr)tr.classList.add('sel');$('pn').textContent=d.n;$('pnote').textContent=d.note+' · '+d.st;$('prole').value=d.role||'Viewer';$('psince').textContent=d.since?'since '+d.since:'no active assignment';$('peall').checked=!d.eff;$('per').checked=!!d.eff;document.querySelectorAll('#peffs input').forEach(function(c){c.checked=!d.eff||d.eff.indexOf(+c.value)>=0;c.disabled=!d.eff});$('pov').innerHTML=li(d.ov);$('pra').innerHTML=li(d.ra);$('saved').textContent=''}document.querySelectorAll('#ut tbody tr').forEach(function(r){r.addEventListener('click',function(e){if(e.target.tagName!=='A')show(+r.getAttribute('data-k'))})});['peall','per'].forEach(function(i){$(i).addEventListener('change',function(){document.querySelectorAll('#peffs input').forEach(function(c){c.disabled=$('peall').checked})})});['psave','psus','addu'].forEach(function(i){$(i).addEventListener('click',function(){$('saved').textContent='Demo only: nothing is saved (static site).'})});$('uf').addEventListener('input',function(){var v=this.value.toLowerCase();document.querySelectorAll('#ut tbody tr').forEach(function(r){r.hidden=v&&r.textContent.toLowerCase().indexOf(v)<0})});var c=D.findIndex(function(d){return d.eff});show(c<0?0:c)})();</script>" % json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        return h
    def register_html(s, frm, t, rs):
        I = s.I; skip = {"id", "type", "schema_version", "title", "hub", "created_by", "modified_by", "origin", "access_marking", "verified_by", "verified_at", "x_phase3", "links"}
        def val(v):
            if isinstance(v, str):
                if v.startswith("user:"): return s.ul(frm, v)
                return s.rl(frm, v) if re.match(r"^[A-Z]{2,3}-(D|FW)-\d{7}(@\d+)?$", v) else (s.link(frm, v) if v in s.url else E(v))
            if isinstance(v, list): return ", ".join(val(x) for x in v[:30]) + (" …" if len(v) > 30 else "")
            if isinstance(v, dict):
                if set(v) >= {"from", "to"} and isinstance(v["to"], int): return rng(v)
                return "; ".join("%s: %s" % (E(k), val(x)) for k, x in v.items())
            return E(str(v))
        h = "<p><label>Filter rows: <input type='search' class='rf'></label></p><table class='reg'><thead><tr><th scope=col>ID</th><th scope=col>Title</th><th scope=col>Status</th><th scope=col>Effectivity</th></tr></thead><tbody>"
        for r in rs:
            e = r.get("effectivity") or r.get("existence")
            if t == "Part Instance":
                idcell = E(r["id"])
            else:
                det = "".join("<dt>%s</dt><dd>%s</dd>" % (E(k), val(v)) for k, v in r.items() if k not in skip)
                det += "".join("<dt>%s</dt><dd>%s</dd>" % (E(l["link_type"]), val(l["target"])) for l in r.get("links", []))
                idcell = "<details><summary>%s</summary><dl class='det'>%s</dl></details>" % (E(r["id"]), det)
            h += "<tr id='%s'><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (E(r["id"]), idcell, E(r["title"]), E(r.get("status", "")), rng(e) if isinstance(e, dict) and "from" in e else "")
        h += "</tbody></table><script>document.querySelectorAll('input.rf').forEach(function(i){i.addEventListener('input',function(){var v=i.value.toLowerCase();document.querySelectorAll('table.reg tbody tr').forEach(function(r){r.hidden=v&&r.textContent.toLowerCase().indexOf(v)<0;});});});if(location.hash){var d=document.getElementById(location.hash.slice(1));if(d){var x=d.querySelector('details');if(x)x.open=true;}}</script>"
        if t == "Part Instance": h = "<p>One row per Part Instance; there is no detail page or panel for an individual Part Instance beyond its row (plan 3.2).</p>" + h
        return h
    def coverage(s, fds):
        I = s.I; h = "<p>For every FDPS, each inherited or direct Requirement and TSM and its Compliance Statements by effectivity range (2.8).</p><table><thead><tr><th scope=col>FDPS</th><th scope=col>Requirement / TSM</th><th scope=col>Positions by range</th></tr></thead><tbody>"
        tot = {"Compliant": 0, "Non-compliant": 0, "Not applicable": 0}
        for f in fds:
            inh = I.inherited(f); cs = I.statements(f)
            if not inh: h += "<tr><td>%s</td><td colspan=2>Nothing inherited yet</td></tr>" % s.rl("reports/coverage/", f["id"], f["fdps_number"])
            for k in sorted(inh):
                rows = sorted([c for c in cs if c["requirement"] == k], key=lambda c: c["effectivity"]["from"])
                for c in rows: tot[c["position"]] = tot.get(c["position"], 0) + 1
                h += "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (s.rl("reports/coverage/", f["id"], f["fdps_number"]), s.rl("reports/coverage/", k, "%s %s" % (I.IDX[k].get("req_number") or I.IDX[k].get("manual_code"), I.IDX[k]["title"])), "; ".join("%s %s" % (rng(c["effectivity"]), E(c["position"])) for c in rows) or "<b>No statement</b>")
        return "<p>Statements: %s.</p>" % ", ".join("%s %d" % (k, v) for k, v in tot.items()) + h + "</tbody></table>"
    def gate_report(s, fds, effs):
        I = s.I; h = "<p>Release gate (6C.11, 6A.17): C pass, every Action from reviews A, B and C closed and accepted, and no Non-compliant Compliance Statement over the revision's range.</p>" + s.eff_table("reports/release-gate/", fds, effs)
        h += "<table><thead><tr><th scope=col>FDPS revision</th><th scope=col>Effectivity</th><th scope=col>Status</th><th scope=col>Gate attempts</th><th scope=col>Confirmation</th></tr></thead><tbody>"
        for f in fds:
            for r in I.revisions(f):
                h += "<tr><td>%s rev %s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (s.rl("reports/release-gate/", f["id"], f["fdps_number"]), E(r["revision"]), rng(r["effectivity"]), E(r["status"]), "; ".join("%s %s" % (x["at"][:10], E(x["result"])) for x in r.get("gate_attempts", [])) or "none", E((r.get("gate_confirmation") or {}).get("at", "")[:10]))
        return h + "</tbody></table>"
    def feedback(s):
        I = s.I; r16 = s.r16
        h = "<p>Gaps and findings recorded while filling the Demo; they feed the next framework version (plan 3.2).</p><h2>R-16: Supports and Secures links into a Sub-structure FDPS</h2>"
        for k, v in r16.items():
            h += "<p>%s: Systems physically mounted on it through other FDPSs' Supports or Secures links: %s. Not prompted by its Sub-structure lists: <b>%s</b>. Inherited but with no mounted item in the current population (over-inclusion, agreed at reviews as no physical interface): %s.</p>" % (
                s.rl("feedback/", k, I.IDX[k]["fdps_number"]), ", ".join("%s (%s)" % (s.link("feedback/", y), ", ".join(E(x) for x in xs)) for y, xs in v["mounted"].items()) or "none", ", ".join(s.link("feedback/", y) for y in v["not_prompted"]) or "none", ", ".join(s.link("feedback/", y) for y in v["inherited_not_mounted"]))
        h += s.site_cfg.get("feedback_html", "")
        return h
def main():
    a = argparse.ArgumentParser(); a.add_argument("--framework", required=True); a.add_argument("--project", required=True); a.add_argument("--schema"); a.add_argument("--out", required=True); a.add_argument("--repo"); a.add_argument("--old", required=True); a.add_argument("--fw-old", default=os.path.join(HERE, "..", "site", "v08_ids.json")); o = a.parse_args()
    res, info, st = validate.gate(o.framework, o.project, o.schema, o.repo)
    if not all(r[2] for r in res): print("Gate failed; site not generated."); [print("FAIL", r[1]) for r in res if not r[2]]; sys.exit(1)
    build_site.VERSION_LABEL = "Demo Production Hub v1.1-demo · Framework %s" % json.load(open(o.framework))["meta"]["framework_version"] if o.framework.endswith(".json") else build_site.VERSION_LABEL
    build_site.DEMO = build_site.FW_HOME = FW_URL
    tmp = o.out.rstrip("/") + ".tmp"; I = Infer(st)
    s = Demo(st, tmp, I); s.site_cfg = json.load(open(os.path.join(o.project, "site.json"))) if os.path.exists(os.path.join(o.project, "site.json")) else {}; s.r16 = info.get("r16", {}); s.build()
    s.make_aliases(json.load(open(o.fw_old)))
    old = json.load(open(o.old)); A = s.aliases
    for k, v in old.get("aliases", {}).items(): A[k] = v
    for p in old["pages"]:
        if p["id"] in A: continue
        A[p["id"]] = {"PR": "records/part-definitions/", "PI": "records/part-instances/", "REQ": "records/requirements/", "VER": "records/verifications/", "ISS": "records/issues/", "FS": "records/finish-specifications/"}.get(p["id"].split("-")[0], "retired/")
    s.compute_backlinks(); s.render(); shutil.copy(os.path.join(build_site.SITE, "fuel-feed.svg"), os.path.join(tmp, "assets", "fuel-feed.svg"))
    # demo pages: relabel header link text and footer
    for root, _, files in os.walk(tmp):
        for fn in files:
            if fn.endswith((".html", ".js")):
                fp = os.path.join(root, fn); t = open(fp, encoding="utf-8").read()
                t = t.replace("{PROJ}", "Project " + I.PRJ.get("project_letter", "")).replace("{PNAME}", I.PRJ.get("name", ""))
                t = t.replace("Engineering Hub · Framework</a>", "Engineering Hub · Demo Production Hub</a>").replace("· Engineering Hub Framework</title>", "· Demo Production Hub (fictional)</title>")
                t = t.replace("Generic framework content only; no project data. <a href=\"%s\">Demo Production Hub (fictional)</a>" % FW_URL, "Project " + I.PRJ.get("project_letter", "") + " is entirely fictional. <a href=\"%s\">Engineering Hub Framework</a>" % FW_URL)
                t = t.replace("/engineering-hub/", "/engineering-hub-demo/") if fn == "404.html" else t
                open(fp, "w", encoding="utf-8").write(t)
    w = build_site.checks(s, tmp, o.repo, project=True)
    fdp = [p for p in s.pages if p.startswith("fdps/") and p != "fdps/"]
    w.append(("W", "One FDPS page per FDPS and no page for any Part Instance (plan 3.2)", len(fdp) == len(I.of("FDPS")) and not any(re.search(r"pi-d-|part-instances/.+/", p) for p in s.pages), fdp))
    blocked = [c for c in I.of("Compliance Statement") if c["position"] == "Non-compliant"]
    t17 = "".join(open(os.path.join(tmp, s.url[c["fdps"]], "index.html")).read() for c in blocked)
    w.append(("W", "FDPS pages show 'Release blocked' for every Non-compliant range (decision 9)", blocked and t17.count("Release blocked") >= 1))
    rd = lambda p: open(os.path.join(tmp, p, "index.html"), encoding="utf-8").read()
    w.append(("W", "One page per EDR and per TSM, each listing its line items or statements and the inheriting FDPSs (5.22)", all(s.url[d["id"]] in s.pages and "Line items (" in rd(s.url[d["id"]]) for d in I.edrs()) and all(s.url[t["id"]] in s.pages and "Statements (" in rd(s.url[t["id"]]) for t in I.of("TSM"))))
    li = {I.IDX[q]["req_number"] for q in I.IDX if q.startswith("REQ-")}
    above = [p for p in s.pages if re.match(r"^systems/[^/]+/([^/]+/)?$", p) and any(n in rd(p) for n in li)]
    w.append(("W", "Pages above FDPS level list EDR and TSM documents as links, never line items (5.21)", not above, above[:5]))
    fds = I.of("FDPS")
    nost = [f["id"] for f in fds if not all(("Line items (" in rd(s.url[f["id"]]), "Maturity:" in rd(s.url[f["id"]])))]
    w.append(("W", "FDPS pages list every inherited line item with its state (Inherited, Kept, Broken, Superseded (auto)) and maturity (5.27)", not nost and all(x in "".join(rd(s.url[f["id"]]) for f in fds) for x in (">Kept<", ">Broken<", ">Superseded (auto)<")), nost))
    w.append(("W", "One user page per User (placeholder) and an admin page with user list, edit panel and a clear demo-only notice (5A.8, 5A.9)", all(s.url[u["handle"]] in s.pages for u in I.of("User")) and "Demo UI only." in rd("admin/users/") and "ADMIN_USERS" in rd("admin/users/")))
    own = [r["id"] for r in I.R if r.get("hub") not in ("FW", None) and r.get("owner") and r["owner"] not in s.url]
    w.append(("W", "Every Owner and Contributor links to a user page (5A.7)", not own, own[:5]))
    for r in w: print(("PASS" if r[2] else "FAIL"), r[1], "" if r[2] else str(r[3])[:300])
    if not all(r[2] for r in w): print("Site checks failed; output left in", tmp); sys.exit(1)
    if os.path.exists(o.out): shutil.rmtree(o.out)
    os.rename(tmp, o.out)
    print("Demo site: %d pages written to %s; gate %d/%d, site checks %d/%d" % (len(s.pages), o.out, sum(r[2] for r in res), len(res), sum(r[2] for r in w), len(w)))
if __name__ == "__main__": main()
