"""Static site generator (plan 2.4 steps 7 and 8). Runs the gate, generates the Framework
Hub pages from registers, Design Considerations and Hub Page records, then crawls the
output (every internal link resolves, required panels present, page counts, colour
contrast, purity of the output). Writes nothing usable unless every check passes.
Usage: build_site.py --framework data/framework --out docs [--repo .]"""
import argparse, html, json, os, re, shutil, sys, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import validate, purity
SITE = os.path.join(HERE, "..", "site")
VERSION_LABEL = "Framework v1.0 (release candidate 1.0.0-rc.3)"
DEMO = "https://danielwagner69.github.io/engineering-hub-demo/"
E = html.escape
def slug(s): return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and"))).strip("-")
ENTRY = {"A": ["Allocated Requirements and interfacing Systems identified", "Concept layout in the integrated model", "Risks and design options recorded"],
         "B": ["Stage A passed and its Actions closed or planned", "Preliminary sizing and routing in the integrated model", "Applicable TSMs identified with their applicable statements"],
         "C": ["Stage B passed and its Actions closed or planned", "Detail definitions ready for release", "Compliance Statements recorded for every inherited and direct Requirement and TSM", "Verification evidence complete or planned"]}

class Site:
    def __init__(self, st, out):
        self.st = st; self.out = out; self.pages = {}; self.index = []
        self.REG = {e["id"]: e for e in st["register_entries"]}; self.by = {}
        for e in st["register_entries"]: self.by.setdefault(e["register"], []).append(e)
        for v in self.by.values(): v.sort(key=lambda e: e.get("sort_order", 0))
        self.R = st["records"]; self.url = {}
    def page_of(self, node):
        return next(p for p in self.R if p["type"] == "Hub Page" and p.get("framework_node") == node and p.get("hub") == "FW")
    def kids(self, reg, parent): return [e for e in self.by.get(reg, []) if e.get("parent") == parent]
    def lab(self, i): return self.REG[i]["label"] if i in self.REG else i
    def link(self, frm, i, text=None):
        u = self.url.get(i); t = E(text or self.lab(i))
        return '<a href="%s">%s</a>' % (self.rel(frm, u), t) if u else t
    def rel(self, frm, to):
        depth = 0 if frm == "" else frm.strip("/").count("/") + 1
        return ("../" * depth) + to if to else ("../" * depth or "./")
    def add(self, path, title, body, rid, kind, crumbs=(), meta=None, trees=None, preview=False, text=""):
        assert path not in self.pages, path
        self.pages[path] = dict(title=title, body=body, rid=rid, kind=kind, crumbs=list(crumbs), meta=meta or {}, trees=trees or [], preview=preview)
        self.index.append({"id": rid, "t": title, "u": path, "x": re.sub(r"<[^>]+>", " ", text or body)[:600]})
    # ---- URL plan
    def plan(self):
        U = self.url; B = self.by
        for e in B["SCOPE"]: U[e["id"]] = "product-scopes/%s/" % slug(e["label"])
        for m in B["MU"]:
            U[m["id"]] = "manufacturing/%s/" % slug(m["label"])
            for b in self.kids("BS", m["id"]): U[b["id"]] = U[m["id"]] + slug(b["code"].split("-")[-1] + "-" + re.sub(r"^.*?(BS\d|FA\d|Bench)\s*", "", b["label"])) + "/"
        for t in B["DT"]:
            U[t["id"]] = "design/%s/" % slug(t["label"])
            for s in self.kids("DST", t["id"]): U[s["id"]] = U[t["id"]] + slug(s["label"]) + "/"
        for g in B["SG"]: U[g["id"]] = "system-groups/%s/" % slug(g["label"])
        for y in B["SYS"]:
            U[y["id"]] = "systems/%s/" % slug(y["label"])
            for s in self.kids("SUB", y["id"]): U[s["id"]] = U[y["id"]] + ("general" if s.get("is_catch_all") else slug(s["label"])) + "/"
        for l in B["LCS"]: U[l["id"]] = "lifecycle/%d-%s/" % (l["sequence_no"], slug(l["label"]))
        for s in B["STAGE"]: U[s["id"]] = "reviews/stage-%s-%s/" % (s["code"].lower(), slug(s["label"]))
        for d in B["DISC"]: U[d["id"]] = "disciplines/%s/" % slug(d["label"].split(" (")[0])
        for r in B: U["register:" + r] = "registers/%s/" % slug(r)
        for p in self.R:
            if p["type"] == "Hub Page" and p.get("slug"): U[p["id"]] = p["slug"] + "/"
            if p["type"] == "Lesson Learned": U[p["id"]] = "lessons/#" + p["id"]
            if p["type"] == "Design Consideration": U[p["id"]] = U[p["discipline"]]
        for k, v in {"DTY": "part-attributes/design-types/", "SRC": "part-attributes/sources/", "SAF": "part-attributes/safety-classification/", "PROP": "part-attributes/item-properties/"}.items():
            U["attr:" + k] = v
            for e in B[k]: U[e["id"]] = v + "#" + e["id"]
    # ---- shared panels
    def metap(self, rid, owner="Framework owner", vs="Unverified (generic framework content, not yet content-reviewed)", reviewed="2026-10-12", extra=None):
        d = {"Permanent ID": rid, "Owner": owner, "Verification status": vs, "Last reviewed": reviewed}; d.update(extra or {}); return d
    def regrow(self, frm, es, cols):
        h = "<table><thead><tr>" + "".join("<th scope=col>%s</th>" % E(c) for c, _ in cols) + "</tr></thead><tbody>"
        for e in es: h += "<tr id='%s'>" % E(e["id"]) + "".join("<td>%s</td>" % f(e) for _, f in cols) + "</tr>"
        return h + "</tbody></table>"
    def build(self):
        self.plan(); U = self.url; B = self.by; L = self.link
        dc = {r["discipline"]: r for r in self.R if r["type"] == "Design Consideration"}
        hubp = {p["slug"]: p for p in self.R if p["type"] == "Hub Page" and p.get("slug")}
        ph = '<span class="badge ph">Placeholder (generic, fictional)</span>'
        # Home
        cards = [("Manufacturing tree", "manufacturing/", "%d Major Units, %d Build Stations" % (len(B["MU"]), len(B["BS"]))), ("Design tree", "design/", "%d Design Teams, %d Sub-teams" % (len(B["DT"]), len(B["DST"]))),
                 ("System tree", "systems/", "%d System Groups, %d Systems, %d Sub-systems" % (len(B["SG"]), len(B["SYS"]), len(B["SUB"]))), ("Lifecycle", "lifecycle/", "%d stages, 4 to 6 in scope" % len(B["LCS"])),
                 ("Disciplines", "disciplines/", "%d Disciplines with Draft checklists" % len(B["DISC"])), ("Product Scope", "product-scopes/", "%d scopes" % len(B["SCOPE"])),
                 ("Design reviews", "reviews/", "Stages A, B, C and the release gate"), ("Registers", "registers/", "%d value registers" % len(B))]
        body = "<p>The Engineering Hub framework: generic, project-independent guidance and controlled registers for designing aircraft installations. Every item is stored once with a permanent identifier and reached through three trees (Manufacturing, Design and System) and cross-cutting views (Lifecycle, Product Scope, Discipline).</p>"
        body += '<div class="cards">' + "".join('<a class="card" href="%s"><div class="n">%s</div><div>%s</div></a>' % (u, E(t), E(d)) for t, u, d in cards) + "</div>"
        body += '<h2>How to read this Hub</h2><ul><li>Hub levels (Full Aircraft down to Build Station, Design Sub-team and Sub-system) are pages. There are no pages for individual parts or Part Instances; those live in a Production Hub.</li><li>Annex A lists (Major Units, Build Stations, Sub-systems, Design Teams, Design Types, Safety Classification, applicability, Type codes) are %s starter values; each project replaces them through Tailoring Records.</li><li>Rules pages: <a href="rules/requirements/">Requirements</a>, <a href="rules/tsms/">TSMs</a>, <a href="rules/compliance/">Compliance</a>, <a href="rules/verification/">Verification</a>, <a href="rules/effectivity/">Effectivity</a>, <a href="rules/revisions-and-numbering/">Numbering</a>, <a href="rules/baselines/">Baselines</a>, <a href="rules/interfaces/">Interfaces</a>, <a href="issues/escalation/">Issue escalation</a>, <a href="lessons/">Lessons Learned</a>, <a href="part-attributes/">Part attributes</a>.</li></ul>' % ph
        body += '<h2>Demo Production Hub</h2><p>See the framework applied to an entirely fictional project: <a href="%s">Demo Production Hub (Sparrow Light Trainer, fictional)</a>. The Demo (v1.1-demo) is built on this framework version.</p>' % DEMO
        body += '<h2>Version</h2><p>%s. Framework Version record FV-FW-0000001: content review not yet done (due before release 1.0.0). See <a href="versions/">version log</a> and <a href="framework-vs-production/">Framework vs Production</a>. Links from v0.8 (<code>#/p/…</code>) redirect to their v1.0 page.</p>' % E(VERSION_LABEL)
        self.add("", "Engineering Hub: Framework", body, "FV-FW-0000001", "home", meta=self.metap("FV-FW-0000001"))
        # Product Scopes
        sys_by_scope = lambda s: [y for y in B["SYS"] if s in y.get("applies_to_scopes", [])]
        self.add("product-scopes/", "Product Scopes", "<p>Product Scope is facet level 0. Each System records the Product Scopes it applies to (2F.11).</p><ul>" + "".join("<li>%s: %s</li>" % (L("product-scopes/", e["id"]), E(e["definition"])) for e in B["SCOPE"]) + "</ul>", "VR-SCOPE", "index", crumbs=[("", "Home")], meta=self.metap("register SCOPE"))
        for e in B["SCOPE"]:
            p = U[e["id"]]; ys = sys_by_scope(e["id"])
            self.add(p, e["label"], "<p>%s</p><h2>Applicable Systems (%d) %s</h2><ul>%s</ul>" % (E(e["definition"]), len(ys), ph, "".join("<li>%s</li>" % L(p, y["id"]) for y in ys)), e["id"], "scope", [("", "Home"), ("product-scopes/", "Product Scopes")], self.metap(e["id"]), trees=[("Product Scope", e["label"])])
        # Manufacturing tree
        mfa = "manufacturing/"
        self.add(mfa, "Manufacturing tree: Full Aircraft", "<p>Full Aircraft &gt; Major Unit &gt; Build Station. Items directly below an FDPS are Located at an aircraft Build Station; Part Instances within an Assembly Instance are Located at the Bench of the same Major Unit (1.6.1, 2C.12). Major Unit is inferred, never stored on the item. %s</p><ul>%s</ul>" % (ph, "".join("<li>%s (%d Build Stations)</li>" % (L(mfa, m["id"]), len(self.kids("BS", m["id"]))) for m in B["MU"])), "TREE-MFG", "tree", [("", "Home")], self.metap("TREE-MFG"), trees=[("Manufacturing", "Full Aircraft")], preview=True)
        for m in B["MU"]:
            p = U[m["id"]]; ks = self.kids("BS", m["id"])
            self.add(p, m["label"], "<p>%s %s</p><h2>Build Stations</h2>%s<h2>Completeness rule</h2><p>Every item of the Major Unit is Located at exactly one of its Build Stations; the Bench holds the Part Instances of Assembly Instances built off-aircraft (2C.11, 2C.12).</p>" % (E(m["definition"]), ph, self.regrow(p, ks, [("Build Station", lambda e: L(p, e["id"])), ("Code", lambda e: E(e["code"])), ("Kind", lambda e: "Bench (off-aircraft)" if e["is_bench"] else "Aircraft")])),
                     m["id"], "tree", [("", "Home"), (mfa, "Manufacturing")], self.metap(m["id"]), trees=[("Manufacturing", "Full Aircraft > " + m["label"])], preview=True)
            for b in ks:
                q = U[b["id"]]
                self.add(q, b["label"], "<p>%s</p><p>%s</p><p>Located at rule: %s</p>" % (E(b["definition"]), ph, "Part Instances within an Assembly Instance of this Major Unit are Located here; the Assembly Instance itself is Located at an aircraft Build Station." if b["is_bench"] else "Items (Part Instances or Assembly Instances) directly below an FDPS are Located at an aircraft Build Station."),
                         b["id"], "tree", [("", "Home"), (mfa, "Manufacturing"), (p, m["label"])], self.metap(b["id"], extra={"Code": b["code"]}), trees=[("Manufacturing", "Full Aircraft > %s > %s" % (m["label"], b["code"]))], preview=True)
        # Design tree
        dfa = "design/"; dcode = {e["code"]: e["id"] for e in B["DISC"]}; dty = {e["label"].split(" (")[0]: e["id"] for e in B["DTY"]}
        self.add(dfa, "Design tree: Full Aircraft", "<p>Full Aircraft &gt; Design Team &gt; Design Sub-team &gt; FDPS (1.4). Design Teams are Hub levels, not facet tags on items: a Part Instance reaches a Design Team only through the FDPS that contains it (2B.8). FDPS pages exist only in a Production Hub. %s</p><ul>%s</ul>" % (ph, "".join("<li>%s: %s</li>" % (L(dfa, t["id"]), ", ".join(L(dfa, s["id"]) for s in self.kids("DST", t["id"]))) for t in B["DT"])), "TREE-DES", "tree", [("", "Home")], self.metap("TREE-DES"), trees=[("Design", "Full Aircraft")], preview=True)
        for t in B["DT"]:
            p = U[t["id"]]; tpg = self.page_of(t["id"]); dts = tpg["applicable_design_types"]; ds = tpg["applicable_disciplines"]
            body = "<p>%s %s</p><h2>Applicable Design Types</h2><p>%s</p><h2>Applicable Disciplines</h2><p>%s</p><p>TSMs reach the team's FDPSs when any tag matches: a Design Type in an FDPS, a System of its home Sub-systems, or a Discipline on this list (6B.5).</p><h2>Design Sub-teams</h2><ul>%s</ul>" % (
                E(t["definition"]), ph, " ".join('<a class="chip" href="%s">%s</a>' % (self.rel(p, U[x]), E(self.lab(x))) for x in dts), " ".join('<a class="chip" href="%s">%s</a>' % (self.rel(p, U[x]), E(self.lab(x))) for x in ds), "".join("<li>%s</li>" % L(p, s["id"]) for s in self.kids("DST", t["id"])))
            self.add(p, "Design Team: " + t["label"], body, t["id"], "tree", [("", "Home"), (dfa, "Design")], self.metap(t["id"]), trees=[("Design", "Full Aircraft > " + t["label"])], preview=True)
            for s in self.kids("DST", t["id"]):
                q = U[s["id"]]
                st_links = "".join("<li>%s</li>" % L(q, g["id"], "Stage %s: %s" % (g["code"], g["label"])) for g in B["STAGE"])
                self.add(q, "Design Sub-team: " + s["label"], "<p>%s %s</p><p>This Sub-team owns its FDPSs (1.7.6). Its page is split into the three review stages (6C.6); each stage section lists default checklist items, the Sign-off team Disciplines and entry criteria. A project tailors these through Tailoring Records.</p><h2>Stage sections</h2><ul>%s</ul>" % (E(s["definition"]), ph, "".join('<li><a href="%sstage-%s/">Stage %s: %s</a></li>' % ("", g["code"].lower(), g["code"], E(g["label"])) for g in B["STAGE"])),
                         s["id"], "tree", [("", "Home"), (dfa, "Design"), (p, t["label"])], self.metap(s["id"]), trees=[("Design", "Full Aircraft > %s > %s" % (t["label"], s["label"]))], preview=True)
                for g in B["STAGE"]:
                    r = q + "stage-%s/" % g["code"].lower(); stid = g["id"]
                    so = next(x for x in self.page_of(s["id"])["stage_sections"] if x["stage"] == stid)["sign_off_disciplines"]
                    rows = []
                    for d in B["DISC"]:
                        for c in dc[d["id"]]["checklists"]:
                            if c["stage"] != stid: continue
                            for it in c["items"]:
                                if it.get("applies_to") and not set(it["applies_to"]) & set(dts): continue
                                rows.append((d, it))
                    tab = "<table><thead><tr><th scope=col>Item</th><th scope=col>Discipline</th><th scope=col>Question</th><th scope=col>State</th></tr></thead><tbody>" + "".join(
                        "<tr><td>%s</td><td>%s</td><td>%s</td><td><span class='badge draft'>%s</span></td></tr>" % (E(it["item_id"]), L(r, d["id"], d["label"].split(" (")[0]), E(it["question"]), E(it["item_status"])) for d, it in rows) + "</tbody></table>"
                    body = "<p>Framework template for the %s stage section of the %s Sub-team page (6C.5, 6C.6), aligned with %s. Default content, %s; items marked Draft are starter content to be reviewed.</p><h2>Entry criteria</h2><ul>%s</ul><h2>Sign-off team Disciplines (agreement required, 6C.19)</h2><p>%s</p><h2>Checklist items (%d)</h2><p>Items of every Discipline for this stage, less items that apply only to Design Types the team does not use (4.4). Disciplines a project marks not applicable are removed in its Production Hub.</p>%s" % (
                        E(g["label"]), E(s["label"]), L(r, g["lifecycle_stage"], "Lifecycle Stage " + self.lab(g["lifecycle_stage"])), ph, "".join("<li>%s</li>" % E(x) for x in ENTRY[g["code"]]), " ".join('<a class="chip" href="%s">%s</a>' % (self.rel(r, U[x]), E(self.lab(x).split(" (")[0])) for x in so), len(rows), tab)
                    self.add(r, "%s: stage %s %s" % (s["label"], g["code"], g["label"]), body, s["id"] + "/" + g["code"], "stage", [("", "Home"), (dfa, "Design"), (p, t["label"]), (q, s["label"])], self.metap(s["id"] + " stage " + g["code"]), trees=[("Design", "Full Aircraft > %s > %s > Stage %s" % (t["label"], s["label"], g["code"]))])
        # System tree
        sfa = "systems/"
        self.add(sfa, "System tree: Full Aircraft", "<p>Full Aircraft &gt; System Group &gt; System &gt; Sub-system (mapping level). Every Part Instance is Homed in exactly one Sub-system, from which its System and System Group are inferred (1.6). The Sub-systems of the structural Systems are Sub-structures.</p>" + "".join("<h2>%s</h2><ul>%s</ul>" % (L(sfa, g["id"]), "".join("<li>%s%s</li>" % (L(sfa, y["id"]), " <span class='badge co'>structural</span>" if y["is_structural"] else "") for y in self.kids("SYS", g["id"]))) for g in B["SG"]), "TREE-SYS", "tree", [("", "Home")], self.metap("TREE-SYS"), trees=[("System", "Full Aircraft")], preview=True)
        for g in B["SG"]:
            p = U[g["id"]]
            self.add(p, "System Group: " + g["label"], "<p>Upper tier of the System facet.</p><ul>%s</ul>" % "".join("<li>%s</li>" % L(p, y["id"]) for y in self.kids("SYS", g["id"])), g["id"], "tree", [("", "Home"), (sfa, "Systems")], self.metap(g["id"]), trees=[("System", "Full Aircraft > " + g["label"])], preview=True)
        for y in B["SYS"]:
            p = U[y["id"]]; kind = "Sub-structure" if y["is_structural"] else "Sub-system"; ks = self.kids("SUB", y["id"])
            body = "<p>%s. A System is a set of items that work together to perform one function (2B.7). Code %s. %s</p><div class='meta'><span class=k>System Group</span><span>%s</span><span class=k>Structural</span><span>%s</span><span class=k>Applies to</span><span>%s %s</span></div><h2>%ss (%d)</h2>%s" % (
                E(y["definition"]), E(y["code"]), "Structural System: its Sub-systems are Sub-structures." if y["is_structural"] else "", L(p, y["parent"]), "Yes" if y["is_structural"] else "No", ", ".join(L(p, s) for s in y["applies_to_scopes"]), ph, kind, len(ks),
                self.regrow(p, ks, [(kind, lambda e: L(p, e["id"])), ("Code", lambda e: E(e["code"])), ("Definition", lambda e: E(e["definition"]))]))
            self.add(p, "System: " + y["label"], body, y["id"], "tree", [("", "Home"), (sfa, "Systems"), (U[y["parent"]], self.lab(y["parent"]))], self.metap(y["id"]), trees=[("System", "Full Aircraft > %s > %s" % (self.lab(y["parent"]), y["label"]))], preview=True)
            for s in ks:
                q = U[s["id"]]
                body = "<p>%s %s</p><h2>Interfacing Systems</h2><table><thead><tr><th scope=col>Interfacing System</th><th scope=col>Reason</th></tr></thead><tbody><tr><td colspan=2>Set per project (6C.20). The list is finite: it never says 'all Systems'.%s</td></tr></tbody></table><p>%s</p>" % (
                    E(s["definition"]), ph, " A non-structural Sub-system page names the structural Systems it attaches to." if not y["is_structural"] else " Every FDPS with a Part Instance homed in this Sub-structure inherits the whole list (over-inclusion accepted).",
                    "Catch-all: holds only items that serve the System as a whole and cannot be placed in a single other %s (2B.11)." % kind if s.get("is_catch_all") else "Requirements allocated here flow to every FDPS with a Part Instance homed in it (6B.2).")
                self.sub_page(s, y, q, kind, body, [("", "Home"), (sfa, "Systems"), (p, y["label"])], trees=[("System", "Full Aircraft > %s > %s > %s" % (self.lab(y["parent"]), y["label"], s["label"]))])
        # Lifecycle
        self.add("lifecycle/", "Lifecycle Stages", "<p>Cross-cutting facet. The current scope is stages 4 to 6; other stages may be tagged now but no stage rules apply to them yet (2B.13).</p><ol>%s</ol>" % "".join("<li>%s%s</li>" % (L("lifecycle/", l["id"]), " <span class='badge so'>in current scope</span>" if l["in_current_scope"] else "") for l in B["LCS"]), "VR-LCS", "index", [("", "Home")], self.metap("register LCS"))
        for l in B["LCS"]:
            p = U[l["id"]]; rs = [g for g in B["STAGE"] if g["lifecycle_stage"] == l["id"]]
            self.add(p, "Lifecycle Stage %d: %s" % (l["sequence_no"], l["label"]), "<p>Stage %d of 11. In current scope: %s.</p>%s" % (l["sequence_no"], "Yes" if l["in_current_scope"] else "No (records may be tagged; no stage-specific rules enforced yet)", ("<p>Design review stage: %s.</p>" % L(p, rs[0]["id"], "Stage %s %s" % (rs[0]["code"], rs[0]["label"]))) if rs else ""), l["id"], "lifecycle", [("", "Home"), ("lifecycle/", "Lifecycle")], self.metap(l["id"]), trees=[("Lifecycle", "Stage %d" % l["sequence_no"])])
        # Reviews
        rp = hubp.pop("reviews")
        def blocks(frm, p): return "".join(("<div class='clause'><b>%s</b> %s</div>" % (E(b["clause"]), E(b["text"]))) if b.get("clause") else "<p>%s</p>" % E(b["text"]) for b in p["body"]["blocks"])
        self.add("reviews/", rp["title"], blocks("reviews/", rp) + "<ul>%s<li><a href='release-gate/'>Release gate, carry-forward and re-review</a></li></ul>" % "".join("<li>%s</li>" % L("reviews/", g["id"], "Stage %s: %s" % (g["code"], g["label"])) for g in B["STAGE"]), rp["id"], "rules", [("", "Home")], self.metap(rp["id"], extra={"Source": "Requirements v23"}))
        for g in B["STAGE"]:
            p = U[g["id"]]; n = sum(len(c["items"]) for d in dc.values() for c in d["checklists"] if c["stage"] == g["id"])
            self.add(p, "Review stage %s: %s" % (g["code"], g["label"]), "<p>Aligned with %s. Generic entry criteria:</p><ul>%s</ul><p>Default Sign-off team Disciplines on every Sub-team template: %s, plus stage additions (%s) and the team's own Disciplines.</p><p>%d Draft checklist items across the 26 Disciplines for this stage; see each <a href='%s'>Discipline</a> page or the Sub-team stage pages.</p>" % (
                L(p, g["lifecycle_stage"]), "".join("<li>%s</li>" % E(x) for x in ENTRY[g["code"]]), ", ".join(L(p, x) for x in sorted(set.intersection(*[set(next(y for y in self.page_of(st["id"])["stage_sections"] if y["stage"] == g["id"])["sign_off_disciplines"]) for st in B["DST"]]))), " (placeholder template lists; the team's own Disciplines are added on each Sub-team page)", n, self.rel(p, "disciplines/")), g["id"], "review", [("", "Home"), ("reviews/", "Reviews")], self.metap(g["id"]))
        # Disciplines
        self.add("disciplines/", "Disciplines", "<p>One list of 26 Disciplines; every Discipline is also a design consideration that all designs address (4.2). Sign-off team Disciplines give agreement at the review stages they are listed against; Consideration only Disciplines are checked by the designer.</p>" + self.regrow("disciplines/", B["DISC"], [("Discipline", lambda e: L("disciplines/", e["id"])), ("Type", lambda e: "<span class='badge %s'>%s</span>" % ("so" if e["discipline_type"].endswith("1") else "co", E(self.lab(e["discipline_type"]))))]), "VR-DISC", "index", [("", "Home")], self.metap("register DISC"))
        for d in B["DISC"]:
            p = U[d["id"]]; c = dc[d["id"]]
            secs = "".join("<h2>Stage %s: %s</h2><table><thead><tr><th scope=col>Item</th><th scope=col>Question</th><th scope=col>Topic / applies to</th><th scope=col>State</th></tr></thead><tbody>%s</tbody></table>" % (
                self.REG[s["stage"]]["code"], E(self.lab(s["stage"])), "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td><span class='badge draft'>%s</span></td></tr>" % (E(i["item_id"]), E(i["question"]), E(", ".join(filter(None, [i.get("topic")] + [self.lab(x) for x in i.get("applies_to", [])])) or "All designs"), E(i["item_status"])) for i in s["items"])) for s in c["checklists"])
            ls = [l for l in self.R if l["type"] == "Lesson Learned" and d["id"] in l.get("discipline", [])]
            body = "<p>%s</p><div class='meta'><span class=k>Discipline type</span><span>%s</span><span class=k>Design Consideration</span><span>%s</span></div><div class='note'>Checklist items are Draft starter content: to be reviewed with the framework owner before release 1.0.0.</div><p>%s</p>%s<h2>Governing TSM</h2><p>Set per project: a project's TSMs tagged with this Discipline reach the FDPSs of Design Teams that list it (6B.5).</p><h2>Related lessons</h2><ul>%s</ul>" % (
                E(c["description"]), E(self.lab(d["discipline_type"])), E(c["id"]), E(c["guidance"]), secs, "".join("<li><a href='%s'>%s</a></li>" % (self.rel(p, U[l["id"]]), E(l["title"])) for l in ls) or "<li>None yet</li>")
            self.add(p, "Discipline: " + d["label"], body, c["id"], "discipline", [("", "Home"), ("disciplines/", "Disciplines")], self.metap(c["id"], vs=c["verification_status"] + " (Draft)", extra={"Register entry": d["id"]}), trees=[("Discipline", d["label"])], text=body)
        # Part attributes
        pa = hubp.pop("part-attributes")
        self.add("part-attributes/", pa["title"], blocks("", pa) + "<ul>" + "".join("<li><a href='%s'>%s</a></li>" % (U["attr:" + k][len("part-attributes/"):], n) for k, n in [("DTY", "Design Types"), ("SRC", "Sources"), ("SAF", "Safety Classification"), ("PROP", "Item Properties")]) + "</ul>", pa["id"], "rules", [("", "Home")], self.metap(pa["id"]))
        for k, n in [("DTY", "Design Types"), ("SRC", "Sources"), ("SAF", "Safety Classification"), ("PROP", "Item Properties")]:
            p = U["attr:" + k]
            self.add(p, n, "<p>%s</p>%s" % ("Part attribute and filter, not a tree. %s" % (ph if self.by[k][0].get("placeholder") else ""), self.regrow(p, B[k], [("ID", lambda e: E(e["id"])), ("Code", lambda e: E(e["code"])), ("Label", lambda e: E(e["label"])), ("Definition", lambda e: E(e["definition"]))])), "register " + k, "register", [("", "Home"), ("part-attributes/", "Part attributes")], self.metap("register " + k))
        # Rules and reference pages from Hub Page records
        for s, pg in sorted(hubp.items()):
            if s in ("glossary", "lessons", "retired"): continue
            self.add(U[pg["id"]], pg["title"], blocks(U[pg["id"]], pg), pg["id"], "rules", [("", "Home")], self.metap(pg["id"], extra={"Source": "%s (clauses quoted)" % pg.get("origin", {}).get("source_ref", "Requirements v23").replace("Requirements Prompt Draft ", "Requirements ")}))
        gp = hubp["glossary"]
        self.add("glossary/", "Glossary", "<p>%s</p><dl>%s</dl>" % (E(gp["body"]["blocks"][0]["text"]), "".join("<dt><b>%s</b></dt><dd>%s</dd>" % (E(g["term"]), E(g["definition"])) for g in sorted(gp["glossary"], key=lambda g: g["term"].lower()))), gp["id"], "reference", [("", "Home")], self.metap(gp["id"]))
        rt = hubp["retired"]; self.add("retired/", rt["title"], "<p>%s</p><p><a href='../'>Home</a></p>" % E(rt["body"]["blocks"][0]["text"]), rt["id"], "reference", [("", "Home")], self.metap(rt["id"]))
        lp = hubp["lessons"]; LLs = sorted([l for l in self.R if l["type"] == "Lesson Learned"], key=lambda l: l["id"])
        lb = blocks("lessons/", lp) + "<p><label for='llf'>Filter lessons by any word or tag:</label> <input id='llf' type='search'></p>" + "".join(
            "<article class='ll' id='%s' data-tags='%s'><h2>%s</h2><p class='crumbs'>%s · %s</p><p><b>Summary.</b> %s</p><p><b>What happened.</b> %s</p><p><b>Root cause.</b> %s</p><p><b>Recommendation.</b> %s</p><p><b>Applicability.</b> %s</p><p>%s</p></article>" % (
                E(l["id"]), E(" ".join(self.lab(x) for k in ("lifecycle_stage", "system", "discipline", "design_type", "source", "product_scope", "major_unit") for x in l.get(k, []))), E(l["title"]), E(l["id"]), E(l["status"]),
                E(l["summary"]), E(l["what_happened"]), E(l["root_cause"]), E(l["recommendation"]), E(l["applicability"]),
                " ".join("<span class='chip'>%s</span>" % E(self.lab(x)) for k in ("lifecycle_stage", "system", "discipline", "design_type") for x in l.get(k, []))) for l in LLs)
        lb += "<script>document.getElementById('llf').addEventListener('input',function(e){var v=e.target.value.toLowerCase();document.querySelectorAll('article.ll').forEach(function(a){a.hidden=v&&a.textContent.toLowerCase().indexOf(v)<0;});});</script>"
        self.add("lessons/", "Lessons Learned", lb, lp["id"], "rules", [("", "Home")], self.metap(lp["id"]))
        # Registers
        self.add("registers/", "Registers", "<p>Every categorical field references an entry of a value register (2B.1). Entries are never deleted, only retired; identifiers are permanent.</p>" + self.regrow("registers/", [{"id": r, "n": len(v)} for r, v in sorted(B.items())], [("Register", lambda e: "<a href='%s'>%s</a>" % (slug(e["id"]) + "/", E(e["id"]))), ("Entries", lambda e: str(e["n"]))]), "REGISTERS", "index", [("", "Home")], self.metap("REGISTERS"))
        for r, v in sorted(B.items()):
            p = U["register:" + r]
            self.add(p, "Register: " + r, "<p>%s</p>%s" % (ph if v[0].get("placeholder") else "Framework register.", self.regrow(p, v, [("ID", lambda e: E(e["id"])), ("Code", lambda e: E(e["code"])), ("Label", lambda e: L(p, e["id"]) if e["id"] in U else E(e["label"])), ("Parent", lambda e: L(p, e["parent"]) if e.get("parent") else ""), ("State", lambda e: E(e["state"]))])), "register " + r, "register", [("", "Home"), ("registers/", "Registers")], self.metap("register " + r))
        fv = [x for x in self.R if x["type"] == "Framework Version"][0]
        self.add("versions/", "Framework version log", "<p><b>%s</b> (%s). Content review: %s.</p><ul>%s</ul><p>Previous: v0.8 (prototype), kept as git tag <code>v0.8</code> for rollback.</p>" % (E(fv["title"]), E(fv["id"]), E(fv["content_review"]["state"]), "".join("<li>%s</li>" % E(x) for x in fv["change_list"])), fv["id"], "reference", [("", "Home")], self.metap(fv["id"]))
        self.add("search/", "Search", "<p>Use the Ask the Hub box at the top of every page. Search covers this Framework Hub only (no production data).</p>", "SEARCH", "reference", [("", "Home")], self.metap("SEARCH"))
    # ---- v8 tree-page layout (Requirements v24.6 5.23 to 5.30)
    GROUPS = [("req", "Requirement"), ("ver", "Verification"), ("prod", "Product"), ("con", "Considerations"), ("wk", "Working Data")]
    def cat(self, cid, title, body, n=None, chips=""):
        return dict(id=cid, title=title, body=body, n=n, chips=chips)
    def v8_html(self, path, lead, facts, chips, tiles, groups, img, alt):
        im = '<figure class=mp><div class=mpi><img src="%s" alt="%s"></div><figcaption>%s</figcaption></figure>' % (self.rel(path, "assets/" + img), E(alt), E(alt))
        fx = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (E(k), v) for k, v in facts)
        tl = "".join('<a class="tile%s" href="#cat-%s" data-cat="cat-%s"%s><b>%s</b>%s</a>' % (" bad" if t.get("bad") else "", t["cat"], t["cat"], (' data-sel="%s"' % E(t["sel"])) if t.get("sel") else "", t["n"], E(t["label"])) for t in tiles)
        h = '<div class=sumgrid>%s<div><p class=lead>%s</p><div class=chips>%s</div><dl class=facts>%s</dl><div class=tiles>%s</div></div></div>' % (im, lead, chips, fx, tl)
        h += '<div class=fstate hidden>Filtered by <b></b><button type=button class=clr>Clear filters</button></div><div class=bar><span class=bl>Page data</span><button type=button class=xall>Expand all</button></div>'
        h += '<div class=key>' + "".join('<span class="k %s">%s</span>' % (k, E(n)) for k, n in self.GROUPS) + '<span class=hint>Categories are collapsed: select one to open it</span></div><div class=zones>'
        for k, n in self.GROUPS:
            h += '<section class="zone %s" aria-label="%s"><h2>%s</h2>' % (k, E(n), E(n))
            for c in groups.get(k, []):
                h += '<details class=cat id="cat-%s"><summary><span class=ct>%s</span><span class=cc><span class="chip cnt">%s</span>%s</span></summary><div class=cb>%s<p class="empty fempty" hidden>Nothing here matches the filters.</p></div></details>' % (c["id"], E(c["title"]), "" if c["n"] is None else c["n"], c["chips"], c["body"])
            h += "</section>"
        return h + "</div>"
    def filter_opts(self):
        B = self.by
        return [("scope", "Product Scope", [(e["id"], e["label"]) for e in B["SCOPE"]]), ("eff", "Effectivity", []), ("lcs", "Lifecycle Stage", [(e["id"], e["label"]) for e in B["LCS"]]),
                ("disc", "Discipline", [(e["id"], e["label"].split(" (")[0]) for e in B["DISC"]]), ("dty", "Design Type", [(e["id"], e["label"].split(" (")[0]) for e in B["DTY"]])]
    def sub_groups(self, sub, sys_, path, fw_body):
        """Framework content of a Sub-system page in the five page groups; a Production Hub overrides this with its data."""
        L = self.link; ph = '<span class="badge ph">Placeholder (generic, fictional)</span>'
        so = [d for d in self.by["DISC"] if d["discipline_type"].endswith("1")]
        ls = [l for l in self.R if l["type"] == "Lesson Learned" and (sys_["id"] in l.get("system", []) or "ALL" in l.get("system", []))]
        lrow = lambda l: "<li data-row data-lcs='%s' data-disc='%s' data-dty='%s'><a href='%s'><b>%s</b></a> %s</li>" % (" ".join(l.get("lifecycle_stage", [])), " ".join(l.get("discipline", [])), " ".join(l.get("design_type", []) or ["ALL"]), self.rel(path, self.url[l["id"]]), E(l["id"]), E(l["title"]))
        G = {"req": [self.cat("edrs", "EDRs", "<p>Set per project: the EDRs tagged to this %s are listed here as documents, each a link to its EDR page (5.21, 6B.2). Line items are shown only on FDPS pages.</p>" % E(sub["label"]), 0),
                     self.cat("tsms", "TSMs", "<p>Set per project: TSMs reach this %s through its applicable Design Types (route Sub-system &gt; Design Type &gt; TSM, 6B.5), and through System and Discipline tags. Each TSM is listed as a document link.</p>" % E(sub["label"]), 0)],
             "ver": [self.cat("compliance", "Compliance", "<p>Per project: a compliance summary per document and per FDPS (5.21).</p>", 0), self.cat("verifications", "Verifications", "<p>Per project: Verification records of the FDPSs linked to this page.</p>", 0),
                     self.cat("reviews", "Reviews", "<p>Per project: Design Reviews covering FDPSs linked here. See <a href='%s'>design reviews</a>.</p>" % self.rel(path, "reviews/"), 0)],
             "prod": [self.cat("fdps", "FDPSs", "<p>FDPS pages exist only in a Production Hub. On a Sub-system page the Product group lists only the linked FDPSs, each with its status and Build Stations; Part Instances are listed on FDPS pages (5.21, 5.24).</p>", 0)],
             "con": [self.cat("ifs", "Interfacing Systems", fw_body, None, ph), self.cat("disc", "Disciplines and Stakeholders", "<ul class=rows>%s</ul>" % "".join("<li data-row data-disc='%s'>%s</li>" % (d["id"], L(path, d["id"], d["label"].split(" (")[0])) for d in so), len(so))],
             "wk": [self.cat("issues", "Issues", "<p>Per project: open Issues affecting this %s. See <a href='%s'>Issue escalation</a>.</p>" % (E(sub["label"]), self.rel(path, "issues/escalation/")), 0),
                    self.cat("lessons", "Lessons Learned", ("<ul class=rows>%s</ul>" % "".join(lrow(l) for l in ls)) if ls else "<p>No framework lesson is tagged to this System yet. Lessons are matched by tag (Lifecycle Stage, Discipline, Design Type, System, optionally Sub-system), not by keyword (2G.3).</p>", len(ls))]}
        tiles = [dict(label="FDPS", n=0, cat="fdps"), dict(label="EDRs", n=0, cat="edrs"), dict(label="TSMs", n=0, cat="tsms"), dict(label="Non-compliant", n=0, cat="compliance"), dict(label="Open Issues", n=0, cat="issues"), dict(label="Lessons", n=len(ls), cat="lessons")]
        return G, tiles, [], "model-placeholder.svg", "Model preview: image placeholder until the live model is available (1.12, 5.16)", "Framework template: a Production Hub shows its data here."
    def sub_page(self, sub, sys_, path, kind, fw_body, crumbs, trees):
        meta = self.metap(sub["id"], **self.sub_meta(sub))
        G, tiles, chips, img, alt, note = self.sub_groups(sub, sys_, path, fw_body)
        facts = [("Parent", "%s › %s" % (self.link(path, sys_["id"]), self.link(path, sys_["parent"]))), ("Design Lead (owner)", self.sub_owner(sub, path)), ("Design Sub-team", self.sub_team(sub, path)),
                 ("ID", '<a href="%s#%s">%s</a>' % (self.rel(path, self.url["register:SUB"]), E(sub["id"]), E(sub["id"]))), ("Verification status", E(meta["Verification status"])), ("Last reviewed", E(meta["Last reviewed"]))]
        ch = '<span class="chip">%s</span>%s%s' % (E(kind), " <span class='chip mid'>Catch-all</span>" if sub.get("is_catch_all") else "", "".join(chips))
        lead = "%s %s" % (E(sub["definition"]), E(note))
        self.add(path, "%s: %s" % (kind, sub["label"]), self.v8_html(path, lead, facts, ch, tiles, G, img, alt), sub["id"], "v8", crumbs, meta, trees=trees, preview=False, text=sub["label"] + " " + sub["definition"])
        self.pages[path]["v8"] = True
    def sub_meta(self, sub): return {}
    def sub_owner(self, sub, path): return "Set per project: the Design Lead from the Role register (5.30)"
    def sub_team(self, sub, path): return "Set per project"
    def rail(self, path):
        R = self.rel(path, "")
        f = "".join('<label class=f><span>%s</span><select data-f=%s><option value="">All</option>%s</select></label>' % (E(n), k, "".join('<option value="%s">%s</option>' % (E(v), E(t)) for v, t in opts)) for k, n, opts in self.filter_opts())
        t = ""
        for g in self.by["SG"]:
            ys = self.kids("SYS", g["id"]); og = any(path.startswith(self.url[y["id"]]) for y in ys)
            t += "<li><details%s><summary>%s</summary><ul>" % (" open" if og else "", E(g["label"]))
            for y in ys:
                oy = path.startswith(self.url[y["id"]])
                t += '<li><details%s><summary><a href="%s">%s</a></summary><ul>%s</ul></details></li>' % (" open" if oy else "", R + self.url[y["id"]], E(y["label"]), "".join('<li><a href="%s"%s>%s</a></li>' % (R + self.url[s["id"]], ' aria-current="page"' if self.url[s["id"]] == path else "", E(s["label"])) for s in self.kids("SUB", y["id"])))
            t += "</ul></details></li>"
        return '<aside class=rail aria-label="Navigation and filters"><section class=filters><h2>Filters</h2>%s<button type=button class=reset>Reset filters</button></section><nav class=navtree aria-label="System tree"><h2>System tree</h2><ul class=tree>%s</ul><h2 style="margin-top:14px">Hub</h2><ul class=tree><li><a href="%s">Home</a></li>%s</ul></nav></aside>' % (f, t, R or "./", "".join('<li><a href="%s">%s</a></li>' % (R + u, E(n)) for _, items in self.NAV[:1] for u, n in items))
    def render_v8(self, path, p):
        R = self.rel(path, "")
        crumbs = " › ".join('<a href="%s">%s</a>' % (R + u, E(t)) for u, t in p["crumbs"])
        return """<!doctype html><html lang="en" data-root="%s" data-theme="company"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s · Engineering Hub Framework</title><link rel="stylesheet" href="%sassets/v8.css"><script src="%sassets/v8.js"></script></head>
<body><a class="skip" href="#main">Skip to content</a><header class="top"><button class=rail-btn type=button aria-label="Open navigation">☰</button><a class="brand" href="%s">Engineering Hub · Framework</a><span class="ver">%s</span><span class=sp></span><button class=gear type=button aria-label="Settings" aria-expanded=false>⚙</button>
<div class=settings role=dialog aria-label="Settings"><h3>Theme</h3><label><input type=radio name=th value=company> Company (default)</label><label><input type=radio name=th value=dark> Dark</label><label><input type=radio name=th value=light> Light</label></div></header>
<div class=layout>%s<main id="main"><p class="crumbs">%s</p><h1>%s</h1>%s</main></div>
<form id="ask" class="ask" role="search"><span class=spark aria-hidden=true>✦</span><label for="q" class="skip">Ask the Hub</label><input id="q" type="search" placeholder="Ask the Hub about this page (keyword search)" autocomplete="off"><button type="submit">Ask</button></form><div id="results" aria-live="polite"></div>
<footer class=v8f>%s · Generic framework content only; no project data. <a href="%s">Demo Production Hub (fictional)</a> · <a href="%sversions/">Versions</a></footer>
<script src="%sassets/search-index.js"></script><script src="%sassets/aliases.js"></script><script src="%sassets/ai.js"></script><script src="%sassets/site.js"></script></body></html>""" % (
            R, E(p["title"]), R, R, R, E(VERSION_LABEL), self.rail(path), crumbs, E(p["title"]), p["body"], E(VERSION_LABEL), DEMO, R, R, R, R, R)
    # ---- render
    NAV = [("Trees", [("manufacturing/", "Manufacturing"), ("design/", "Design"), ("systems/", "System")]), ("Views", [("lifecycle/", "Lifecycle"), ("product-scopes/", "Product Scope"), ("disciplines/", "Discipline")]),
           ("Rules", [("reviews/", "Design reviews"), ("rules/requirements/", "Requirements"), ("rules/tsms/", "TSMs"), ("rules/compliance/", "Compliance"), ("rules/verification/", "Verification"), ("rules/effectivity/", "Effectivity"), ("rules/revisions-and-numbering/", "Numbering"), ("rules/baselines/", "Baselines"), ("rules/interfaces/", "Interfaces"), ("rules/edrs-and-line-items/", "EDRs and line items"), ("rules/users-and-access/", "Users and access"), ("part-attributes/", "Part attributes"), ("issues/escalation/", "Issue escalation"), ("lessons/", "Lessons Learned")]),
           ("Reference", [("registers/", "Registers"), ("glossary/", "Glossary"), ("framework-vs-production/", "Framework vs Production"), ("versions/", "Versions")])]
    def render(self):
        if os.path.exists(self.out): shutil.rmtree(self.out)
        os.makedirs(os.path.join(self.out, "assets"))
        for f in ("style.css", "site.js", "ai.js", "v8.css", "v8.js", "model-placeholder.svg"): shutil.copy(os.path.join(SITE, f), os.path.join(self.out, "assets", f))
        open(os.path.join(self.out, "assets", "search-index.js"), "w").write("window.HUB_INDEX=" + json.dumps(self.index, ensure_ascii=False) + ";\n")
        open(os.path.join(self.out, "assets", "aliases.js"), "w").write("window.HUB_ALIASES=" + json.dumps(self.aliases, ensure_ascii=False) + ";\n")
        json.dump(self.aliases, open(os.path.join(self.out, "aliases.json"), "w"), indent=1)
        open(os.path.join(self.out, ".nojekyll"), "w").write("")
        for path, p in self.pages.items():
            R = self.rel(path, "")
            if p.get("v8"):
                d = os.path.join(self.out, path); os.makedirs(d, exist_ok=True); open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(self.render_v8(path, p)); continue
            nav = "".join("<h2>%s</h2><ul>%s</ul>" % (E(h), "".join('<li><a href="%s"%s>%s</a></li>' % (R + u, ' aria-current="page"' if path.startswith(u) else "", E(t)) for u, t in items)) for h, items in self.NAV)
            crumbs = " › ".join('<a href="%s">%s</a>' % (R + u, E(t)) for u, t in p["crumbs"])
            meta = "".join("<span class=k>%s</span><span>%s</span>" % (E(k), E(str(v))) for k, v in p["meta"].items())
            trees = "".join("<span class=k>%s tree</span><span>%s</span>" % (E(a), E(b)) for a, b in p["trees"])
            back = self.backlinks.get(path, [])
            bl = ("<h2>Linked from</h2><ul>%s</ul>" % "".join('<li><a href="%s">%s</a></li>' % (R + u, E(self.pages[u]["title"])) for u in back[:40])) if back else ""
            prev = "<div class='preview' role='note'><b>Live model preview.</b> No production data in the Framework Hub: a Production Hub shows the model filtered to this node and the selected effectivity (1.12, 5.16).</div>" if p["preview"] else ""
            doc = """<!doctype html><html lang="en" data-root="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s · Engineering Hub Framework</title><link rel="stylesheet" href="%sassets/style.css"></head>
<body><a class="skip" href="#main">Skip to content</a><header class="top"><a class="brand" href="%s">Engineering Hub · Framework</a><span class="ver">%s</span>
<form id="ask" role="search"><label for="q" class="skip">Ask the Hub</label><input id="q" type="search" placeholder="Ask the Hub (keyword search)" autocomplete="off"><button type="submit">Ask</button></form></header><div id="results" aria-live="polite"></div>
<div class="wrap"><nav class="side" aria-label="Hub navigation"><ul><li><a href="%s">Home</a></li></ul>%s</nav><main id="main"><p class="crumbs">%s</p><h1>%s</h1><div class="meta" aria-label="Page metadata">%s%s</div>%s%s%s</main>
<footer>%s · Generic framework content only; no project data. <a href="%s">Demo Production Hub (fictional)</a> · <a href="%sversions/">Versions</a></footer></div>
<script src="%sassets/search-index.js"></script><script src="%sassets/aliases.js"></script><script src="%sassets/ai.js"></script><script src="%sassets/site.js"></script></body></html>""" % (
                R, E(p["title"]), R, R, E(VERSION_LABEL), R, nav, crumbs, E(p["title"]), meta, trees, p["body"], prev, bl, E(VERSION_LABEL), DEMO, R, R, R, R, R)
            d = os.path.join(self.out, path); os.makedirs(d, exist_ok=True); open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(doc)
        open(os.path.join(self.out, "404.html"), "w").write('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Not found</title><link rel="stylesheet" href="/engineering-hub/assets/style.css"></head><body><main id="main"><h1>Page not found</h1><p>This address is not part of Framework v1.0. <a href="/engineering-hub/">Go to the Engineering Hub home</a>.</p></main></body></html>')
    def compute_backlinks(self):
        self.backlinks = {}
        for path, p in self.pages.items():
            for h in re.findall(r'href="([^"#:]+)"', p["body"]):
                t = os.path.normpath(os.path.join(path, h)).replace("\\", "/").strip(".") .strip("/")
                t = "" if t in ("", ".") else t + "/"
                if t in self.pages and t != path: self.backlinks.setdefault(t, []).append(path)
        for k in self.backlinks: self.backlinks[k] = sorted(set(self.backlinks[k]))
    def make_aliases(self, old):
        A = {"*": "", "home": "", "HUB-LESSONS": "lessons/", "HUB-GLOSSARY": "glossary/", "HUB-FRAMEWORK": "framework-vs-production/", "HUB-BUILDLEVELS": "manufacturing/", "HUB-FINISH": "registers/fincat/", "HUB-PRODEX": "retired/", "HUB-ISSUES": "retired/"}
        U = self.url; lab = lambda reg: {e["label"].split(" (")[0].lower(): e["id"] for e in self.by[reg]}
        KNLC = {"KN-0001": 2, "KN-0002": 3, "KN-0003": 4, "KN-0004": 5, "KN-0005": 6, "KN-0006": 8, "KN-0007": 9, "KN-0008": 10}
        for k, n in KNLC.items(): A[k] = U["VR-LCS-%04d" % n]
        sysl = lab("SYS"); disl = {e["code"]: e["id"] for e in self.by["DISC"]}
        KNSYS = {"KN-0009": "stores integration", "KN-0010": "cockpit & controls", "KN-0011": "communications", "KN-0012": "crew escape & safety", "KN-0013": "data links", "KN-0014": "electrical power generation & distribution",
                 "KN-0015": "electrical power generation & distribution", "KN-0016": "electronic warfare", "KN-0017": "environmental control", "KN-0018": "flight control", "KN-0019": "flight test instrumentation", "KN-0020": "fuel",
                 "KN-0022": "hydraulics", "KN-0023": "intake & ducts", "KN-0024": "landing gear", "KN-0026": "navigation", "KN-0027": "pneumatics", "KN-0028": "electrical power generation & distribution", "KN-0029": "propulsion",
                 "KN-0030": "radar / sensors", "KN-0031": "skins, doors & panels", "KN-0032": "stores integration", "KN-0033": "primary structure", "KN-0034": "thermal management", "KN-0035": "vehicle management", "KN-0036": "windscreen & canopy"}
        for k, v in KNSYS.items(): A[k] = U[sysl[v]]
        A["KN-0021"] = U["VR-SCOPE-0002"]; A["KN-0025"] = "system-groups/mission-systems/"
        KNDISC = {"KN-0037": "AER", "KN-0038": "AFF", "KN-0039": "AWC", "KN-0040": "AIT", "KN-0041": "AFF", "KN-0042": "EMC", "KN-0043": "EF", "KN-0044": "FUO", "KN-0045": "HF", "KN-0046": "LO", "KN-0047": "MRG", "KN-0048": "MFG",
                  "KN-0049": "MP", "KN-0050": "MEC", "KN-0051": "MBSE", "KN-0052": "SAF", "KN-0053": "SEG", "KN-0054": "SPS", "KN-0055": "SA", "KN-0056": "SLI", "KN-0057": "TST", "KN-0058": "WGT", "KN-0059": "QUA"}
        for k, v in KNDISC.items(): A[k] = U[disl[v]]
        for p in old["pages"]:
            i = p["id"]; pre = i.split("-")[0]; t = p.get("title", "").split(" (")[0].lower()
            if pre == "SYS": A[i] = U[sysl[t]]
            elif pre == "SG": A[i] = U[lab("SG")[t]]
            elif pre == "MU": A[i] = U[lab("MU")[t]]
            elif pre == "PS": A[i] = U[lab("SCOPE")[t]]
            elif pre == "DT": A[i] = "part-attributes/design-types/"
            elif pre == "SRC": A[i] = "part-attributes/sources/"
            elif pre in ("SK", "TR", "EX", "FI"): A[i] = "retired/"
            elif pre == "LL": A[i] = "lessons/"
        for f in old["facets"]:
            A["facet:" + f["key"]] = {"stage": "lifecycle/", "discipline": "disciplines/", "system": "systems/", "productscope": "product-scopes/", "majorunit": "manufacturing/", "designtype": "part-attributes/design-types/", "itemsource": "part-attributes/sources/"}.get(f["key"], "retired/")
        missing = [p["id"] for p in old["pages"] if p["id"] not in A]
        assert not missing, missing
        self.aliases = A
def checks(site, out, repo, project=False):
    res = []
    def chk(n, ok, d=""): res.append(("W", n, bool(ok), d))
    broken = []
    for path in site.pages:
        f = os.path.join(out, path, "index.html"); t = open(f, encoding="utf-8").read()
        for h in re.findall(r'(?:href|src)="([^"]+)"', t):
            if re.match(r"^[a-z]+:", h) or h.startswith("#"): continue
            h = h.split("#")[0]; tgt = os.path.normpath(os.path.join(out, path, h))
            if h.endswith("/") or os.path.isdir(tgt): tgt = os.path.join(tgt, "index.html")
            if not os.path.exists(tgt): broken.append((path, h))
    chk("Crawl: every internal link and asset resolves (plan 2.4 step 8)", not broken, broken[:10])
    bad = [p for p, v in site.pages.items() if not all(k in v["meta"] for k in ("Permanent ID", "Owner", "Verification status", "Last reviewed")) or not v["body"].strip()]
    chk("Every page shows ID, owner, verification status and last reviewed date, and has content (5.5)", not bad, bad[:5])
    B = site.by; cnt = lambda pre: sum(1 for p in site.pages if re.match(pre, p))
    exp = {"Major Units": (cnt(r"^manufacturing/[^/]+/$"), len(B["MU"])), "Build Stations": (cnt(r"^manufacturing/[^/]+/[^/]+/$"), 31), "Design Teams": (cnt(r"^design/[^/]+/$"), 6), "Sub-teams": (cnt(r"^design/[^/]+/[^/]+/$"), 20),
           "Sub-team stage pages": (cnt(r"^design/[^/]+/[^/]+/stage-[abc]/$"), 60), "System Groups": (cnt(r"^system-groups/[^/]+/$"), 7), "Systems": (cnt(r"^systems/[^/]+/$"), 25), "Sub-systems": (cnt(r"^systems/[^/]+/[^/]+/$"), 105),
           "Lifecycle Stages": (cnt(r"^lifecycle/[^/]+/$"), 11), "Review stages": (cnt(r"^reviews/stage-"), 3), "Disciplines": (cnt(r"^disciplines/[^/]+/$"), 26), "Product Scopes": (cnt(r"^product-scopes/[^/]+/$"), 4)}
    chk("One page per Hub level node (plan 3.1 counts)", all(a == b for a, b in exp.values()), {k: v for k, v in exp.items() if v[0] != v[1]})
    def lum(h):
        c = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]; c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]; return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    def cr(a, b): la, lb = sorted([lum(a), lum(b)], reverse=True); return (la + 0.05) / (lb + 0.05)
    pairs = [("#10232E", "#FFFFFF"), ("#00405E", "#FFFFFF"), ("#00405E", "#EAF7F6"), ("#FFFFFF", "#00405E"), ("#00405E", "#9EDEDC"), ("#3E5663", "#EAF7F6"), ("#8A3B12", "#FFF1E8"), ("#5B4300", "#FFF6D6"), ("#00405E", "#F6FBFB"), ("#10232E", "#F6FBFB"),
             ("#00405E", "#E8F0F4"), ("#1D6B69", "#EAF7F6"), ("#4A5A62", "#F2F5F6"), ("#5B3F8C", "#F4F0FA"), ("#7A4E00", "#FBF5E9"), ("#0F5E3A", "#E3F4EC"), ("#3E5663", "#F4F9F9"), ("#10232E", "#F4F9F9"),
             ("#C7B3EE", "#1E1830"), ("#F0C674", "#2A2111"), ("#9FC6DB", "#0E2532"), ("#7FDCD9", "#0C2A2A"), ("#E3EEF0", "#0F2530"), ("#9EDEDC", "#0F2530")]
    low = [(a, b, round(cr(a, b), 2)) for a, b in pairs if cr(a, b) < 4.5]
    chk("Colour contrast of every text/background pair in the stylesheet at least 4.5:1 (WCAG 2.1 AA)", not low, low)
    css = open(os.path.join(SITE, "style.css")).read()
    chk("Brand palette kept (#00405E primary, #46C1BE accent, #9EDEDC light); no external or CDN dependency", all(c in css for c in ("#00405E", "#46C1BE", "#9EDEDC")) and not any(re.search(r'(?:src|href)="https?://(?!danielwagner69\.github\.io)', open(os.path.join(out, p, "index.html"), encoding="utf-8").read()) for p in site.pages))
    allt = "".join(open(os.path.join(out, p, "index.html"), encoding="utf-8").read() for p in site.pages) + open(os.path.join(out, "assets", "search-index.js")).read()
    H = purity.blocked_hashes()
    if project: chk("Built site holds no blocked term (real programme or employer) (6.10)", not purity.blocked_hits(allt, H))
    else: chk("Built site holds no project record identifier and no blocked term (6.10)", not purity.PROJ_ID.search(allt) and not purity.blocked_hits(allt, H), purity.PROJ_ID.findall(allt)[:5])
    chk("Every v0.8 page identifier has a redirect to a v1.0 page", all((t == "" or t in site.pages) for t in site.aliases.values()))
    v8 = [p for p in site.pages if re.match(r"^systems/[^/]+/[^/]+/$", p)]
    bad8 = [p for p in v8 if not site.pages[p].get("v8") or not all(x in open(os.path.join(out, p, "index.html"), encoding="utf-8").read() for x in ('class="zone req"', 'class="zone ver"', 'class="zone prod"', 'class="zone con"', 'class="zone wk"', 'class="ask"', "data-f=eff", 'name=th value=dark', "<details class=cat", "class=rail"))]
    chk("Sub-system pages use the v8 layout: rail filters and tree, preview, five collapsed page groups, fixed Ask bar, theme setting (5.23 to 5.29)", v8 and not bad8, bad8[:5])
    opn = [p for p in v8 if "<details class=cat open" in open(os.path.join(out, p, "index.html"), encoding="utf-8").read()]
    chk("Categories collapsed by default on v8 pages; no dedicated Links area (5.24)", not opn and not any("Linked from</h2>" in open(os.path.join(out, p, "index.html"), encoding="utf-8").read() for p in v8), opn[:3])
    chk("Readable addresses: no permanent identifier in any page path (decision 5)", not [p for p in site.pages if re.search(r"VR-|-FW-\d", p)])
    return res
def main():
    a = argparse.ArgumentParser(); a.add_argument("--framework", required=True); a.add_argument("--project"); a.add_argument("--out", required=True); a.add_argument("--repo"); a.add_argument("--old", default=os.path.join(HERE, "..", "site", "v08_ids.json")); o = a.parse_args()
    if o.project: print("Demo site generation arrives in Phase 3."); sys.exit(2)
    res, info, st = validate.gate(o.framework, repo=o.repo)
    if not all(r[2] for r in res): print("Gate failed; site not generated."); sys.exit(1)
    tmp = o.out.rstrip("/") + ".tmp"
    s = Site(st, tmp); s.build(); s.make_aliases(json.load(open(o.old))); s.compute_backlinks(); s.render()
    w = checks(s, tmp, o.repo)
    for r in w: print(("PASS" if r[2] else "FAIL"), r[1], "" if r[2] else str(r[3])[:300])
    if not all(r[2] for r in w): print("Site checks failed; output left in", tmp); sys.exit(1)
    if os.path.exists(o.out): shutil.rmtree(o.out)
    os.rename(tmp, o.out)
    print("Site: %d pages written to %s; gate %d/%d, site checks %d/%d" % (len(s.pages), o.out, sum(r[2] for r in res), len(res), sum(r[2] for r in w), len(w)))
if __name__ == "__main__": main()
