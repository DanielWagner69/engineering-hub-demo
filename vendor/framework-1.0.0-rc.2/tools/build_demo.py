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
 ("Finish Specification", "finish-specifications"), ("Parameter", "parameters"), ("Parameter Iteration", "parameter-iterations"), ("Effectivity", "effectivities"), ("Tailoring Record", "tailoring-records")]
def rng(e): return "%d to %s" % (e["from"], "open" if e["to"] >= 999 else e["to"])
class Demo(Site):
    def __init__(s, st, out, inf):
        super().__init__(st, out); s.I = inf; s.P = inf.PRJ
        s.PR = [r for r in s.R if r.get("hub") not in ("FW", None) and r["type"] != "Hub Page" or (r["type"] == "Hub Page" and r.get("hub") != "FW")]
    NAV = [("Project", [("fdps/", "FDPSs"), ("records/", "Record registers"), ("reports/coverage/", "Coverage report"), ("reports/release-gate/", "Release gate"), ("reports/open-flags/", "Review Flags"), ("tailoring/", "Tailoring"), ("feedback/", "Framework gaps")])] + Site.NAV
    def page_of(s, node):
        c = [p for p in s.R if p["type"] == "Hub Page" and p.get("framework_node") == node]
        return sorted(c, key=lambda p: p.get("hub") == "FW")[0]
    def rl(s, frm, i, text=None):
        """Link to a record: FDPS page, or its row in the record register."""
        if i is None: return ""
        base = i.split("@")[0]; r = s.I.IDX.get(base)
        if r is None: return s.link(frm, i, text) if i in s.url else E(text or i)
        t = text or i
        if r["type"] == "FDPS": return '<a href="%s">%s</a>' % (s.rel(frm, s.url[base]), E(t))
        reg = dict(TYPES).get(r["type"])
        if r.get("hub") == "FW" or not reg: return s.link(frm, base, t) if base in s.url else E(t)
        return '<a href="%s#%s">%s</a>' % (s.rel(frm, "records/%s/" % reg), E(base), E(t))
    def plan(s):
        super().plan()
        for f in s.I.of("FDPS"): s.url[f["id"]] = "fdps/%s/" % slug(f["fdps_number"])
    # ------------------------------------------------------------------
    def build(s):
        super().build(); I = s.I; U = s.url; L = s.link; R = s.rl
        P = s.P; fds = sorted(I.of("FDPS"), key=lambda f: f["fdps_number"])
        effs = sorted(I.of("Effectivity"), key=lambda e: e["number"])
        ph = '<span class="badge co">{PROJ} (fictional)</span>'
        # ---- project home replaces the framework home
        cs = [c for c in I.of("Compliance Statement")]; openiss = [i for i in I.of("Issue") if i["status"] != "Closed"]; openact = [a for a in I.of("Action") if a["status"] != "Closed"]
        cards = [("FDPSs", "fdps/", len(fds)), ("Part Instances", "records/part-instances/", len(I.of("Part Instance"))), ("Requirements and TSMs", "records/requirements/", len(I.of("Requirement")) + len(I.of("TSM"))),
                 ("Compliance Statements", "reports/coverage/", len(cs)), ("Open Issues", "records/issues/", len(openiss)), ("Open Actions", "records/actions/", len(openact)), ("Design Reviews", "records/design-reviews/", len(I.of("Design Review"))), ("Effectivities", "records/effectivities/", len(effs))]
        body = '<div class="note"><b>Demo content.</b> {PROJ}, {PNAME}, is entirely fictional. Every person, part, requirement, analysis and issue is invented to exercise the Production Hub and is not real engineering data.</div>'
        body += "<p>Production Hub for %s, built on %s (Framework Version %s). Framework pages below carry {PROJ}'s tailoring; production data appears on tree pages, FDPS pages, record registers and reports.</p>" % (E(P["name"]), E(build_site.VERSION_LABEL), E(P["framework_version"]))
        body += '<div class="cards">' + "".join('<a class="card" href="%s"><div class="n">%d</div><div>%s</div></a>' % (u, n, E(t)) for t, u, n in cards) + "</div>"
        body += "<h2>FDPSs</h2>" + s.fdps_table("", fds)
        body += "<h2>Release status by effectivity</h2>" + s.eff_table("", fds, effs)
        body += '<h2>Where to go</h2><ul><li><a href="reports/coverage/">Requirement coverage</a>, <a href="reports/release-gate/">release gate status</a>, <a href="reports/open-flags/">open Review Flags</a></li><li><a href="records/">Record registers</a> and <a href="tailoring/">Tailoring Records</a></li><li><a href="feedback/">Framework gaps found while filling the Demo</a></li><li>Framework (generic, public): <a href="%s">Engineering Hub Framework</a></li></ul>' % FW_URL
        body += "<h2>Masters</h2><p>Part and FDPS revisions are released in the PLM system (release master); the Hub records frozen copies and baselines (6A.13). Effectivity maximum: %d. Effectivity selector with Present / Not present arrives in Phase 4; ranges are shown on every record.</p>" % P.get("effectivity_max", 60)
        s.pages[""].update(title="{PROJ} Production Hub: {PNAME}", body=body, rid=P["id"], meta=s.metap(P["id"], owner=P["owner"], vs=P["verification_status"], reviewed=P["modified_at"][:10]))
        # ---- FDPS index and pages
        s.add("fdps/", "FDPSs", "<p>Every FDPS of {PROJ}. An FDPS is a released installation design package of Part Instances owned by one Design Sub-team (1.7). Part Instances have no pages of their own: they are listed in the FDPS population and the <a href='../records/part-instances/'>Part Instance register</a>.</p>" + s.fdps_table("fdps/", fds), "FDPS", "index", [("", "Home")], s.metap("register FDPS", owner="{PROJ}"))
        for f in fds: s.fdps_page(f, effs)
        # ---- production data on tree pages
        pis = I.of("Part Instance"); ais = I.of("Assembly Instance")
        def inst_rows(frm, items):
            if not items: return "<p>No Part Instance of {PROJ} here yet.</p>"
            h = "<table><thead><tr><th scope=col>Instance</th><th scope=col>Position</th><th scope=col>Part</th><th scope=col>FDPS</th><th scope=col>Located at</th><th scope=col>Homed in</th><th scope=col>Exists</th></tr></thead><tbody>"
            for p in sorted(items, key=lambda x: x["id"]):
                d = (I.lk(p, "Instance of") or [None])[0]; fd = I.fdps_of(p["id"]) or next((I.fdps_of(a["id"]) for a in ais if p["id"] in I.lk(a, "Contains")), None)
                h += "<tr><td id='%s'>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (E(p["id"]), E(p["id"]), E(p.get("position_name", p["title"])), R(frm, d, (I.IDX.get(d) or {}).get("part_number") or d), R(frm, fd, I.IDX[fd]["fdps_number"]) if fd else "", ", ".join(L(frm, x, x if False else None) for x in I.lk(p, "Located at")), ", ".join(L(frm, x) for x in I.lk(p, "Homed in")), rng(p["existence"]))
            return h + "</tbody></table>"
        for sub in s.by["SUB"]:
            path = U[sub["id"]]; here = [p for p in pis if I.lk(p, "Homed in") == [sub["id"]]]
            pg = I.pages.get(sub["id"]); ex = ""
            if pg and pg.get("hub") != "FW":
                ex += "<h2>{PROJ} interface list %s</h2><p>From %s (%s). %s</p><ul>%s</ul>" % (ph, R(path, pg["id"]), E(pg["title"]), "Flows to every FDPS whose lead Sub-system is a Sub-structure with a Part Instance homed here (R-09)." if I.PAR[sub["id"]] in I.STR else "Flows to every FDPS with a Part Instance homed here.", "".join("<li>%s</li>" % L(path, y) for y in pg["interfaces"]))
            fl = sorted({I.fdps_of(p["id"]) for p in here} - {None})
            if here or ex:
                ex += "<h2>Part Instances homed here %s</h2>%s<h2>FDPSs with Part Instances here</h2><ul>%s</ul>" % (ph, inst_rows(path, here), "".join("<li>%s</li>" % R(path, x, "%s %s" % (I.IDX[x]["fdps_number"], I.IDX[x]["title"])) for x in fl) or "<li>None</li>")
                ex += "<h2>Requirements allocated here</h2><ul>%s</ul>" % ("".join("<li>%s</li>" % R(path, r["id"], "%s %s" % (r["req_number"], r["title"])) for r in I.of("Requirement") if sub["id"] in I.lk(r, "Allocated to")) or "<li>None</li>")
                s.pages[path]["body"] += ex
        for bs in s.by["BS"]:
            path = U[bs["id"]]; here = [p for p in pis + ais if bs["id"] in I.lk(p, "Located at")]
            if here: s.pages[path]["body"] += "<h2>Items located here %s</h2>%s" % (ph, inst_rows(path, here))
        for y in s.by["SYS"]:
            path = U[y["id"]]; fl = [f for f in fds if y["id"] in I.systems(f)]
            rq = [r for r in I.of("Requirement") if y["id"] in I.lk(r, "Allocated to")]
            if fl or rq: s.pages[path]["body"] += "<h2>{PROJ} FDPSs with Part Instances in this System %s</h2><ul>%s</ul><h2>Requirements allocated to the System</h2><ul>%s</ul>" % (ph, "".join("<li>%s</li>" % R(path, f["id"], "%s %s" % (f["fdps_number"], f["title"])) for f in fl) or "<li>None</li>", "".join("<li>%s</li>" % R(path, r["id"], "%s %s" % (r["req_number"], r["title"])) for r in rq) or "<li>None</li>")
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
    def register_html(s, frm, t, rs):
        I = s.I; skip = {"id", "type", "schema_version", "title", "hub", "created_by", "modified_by", "origin", "access_marking", "verified_by", "verified_at", "x_phase3", "links"}
        def val(v):
            if isinstance(v, str):
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
    build_site.VERSION_LABEL = "Demo Production Hub v1.0-demo (Phase 3) · Framework %s" % json.load(open(o.framework))["meta"]["framework_version"] if o.framework.endswith(".json") else build_site.VERSION_LABEL
    build_site.DEMO = build_site.FW_HOME = FW_URL
    tmp = o.out.rstrip("/") + ".tmp"; I = Infer(st)
    s = Demo(st, tmp, I); s.site_cfg = json.load(open(os.path.join(o.project, "site.json"))) if os.path.exists(os.path.join(o.project, "site.json")) else {}; s.r16 = info.get("r16", {}); s.build()
    s.make_aliases(json.load(open(o.fw_old)))
    old = json.load(open(o.old)); A = s.aliases
    for k, v in old.get("aliases", {}).items(): A[k] = v
    for p in old["pages"]:
        if p["id"] in A: continue
        A[p["id"]] = {"PR": "records/part-definitions/", "PI": "records/part-instances/", "REQ": "records/requirements/", "VER": "records/verifications/", "ISS": "records/issues/", "FS": "records/finish-specifications/"}.get(p["id"].split("-")[0], "retired/")
    s.compute_backlinks(); s.render()
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
    for r in w: print(("PASS" if r[2] else "FAIL"), r[1], "" if r[2] else str(r[3])[:300])
    if not all(r[2] for r in w): print("Site checks failed; output left in", tmp); sys.exit(1)
    if os.path.exists(o.out): shutil.rmtree(o.out)
    os.rename(tmp, o.out)
    print("Demo site: %d pages written to %s; gate %d/%d, site checks %d/%d" % (len(s.pages), o.out, sum(r[2] for r in res), len(res), sum(r[2] for r in w), len(w)))
if __name__ == "__main__": main()
